"""FastAPI backend for the Campus Customs dashboard.

Start it from the backend/ folder:
    uvicorn main:app --reload --port 8000

Shop data is read and changed through the MCP server (backend/mcp_client.py), the same
tools the agents use. Agents only prepare payments/purchases; POST /api/approve is the
only route that changes cash, and it needs two different humans (maker + checker).
"""

from __future__ import annotations

import asyncio
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:  # so `uvicorn main:app` works when started from backend/
    sys.path.insert(0, str(ROOT))

import json  # noqa: E402

from fastapi import FastAPI, HTTPException, Query  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from backend import audit  # noqa: E402
from backend.agents.base import run_team  # noqa: E402
from backend.config import AUDIT_PATH, MODEL_NAME  # noqa: E402
from backend.mcp_client import call  # noqa: E402
from backend.models import TeamDeps  # noqa: E402

ORIGINAL_DB = ROOT / "data" / "campus_customs.db"
WORKING_DB = ROOT / "data" / "campus_customs_new.db"

app = FastAPI(title="Campus Customs backend")
# Only the Vite dev page (npm run dev, usually http://localhost:5173) may call these routes from a
# browser. Any local port is accepted in case Vite has to move to 5174 when 5173 is busy.
FRONTEND_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
app.add_middleware(CORSMiddleware, allow_origins=FRONTEND_ORIGINS,
                   allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
                   allow_methods=["GET", "POST"], allow_headers=["Content-Type"])

RUNS: dict[str, dict[str, Any]] = {}  # run_id -> {ticket_id, status, report, error, started_at}
_run_lock = asyncio.Lock()  # one team run at a time, so two runs can't race on the same cash


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


async def _mcp(tool: str, **args: Any) -> Any:
    try:
        return await call(tool, **args)
    except Exception as exc:
        raise HTTPException(502, f"MCP tool {tool} failed: {exc}") from exc


# ---------------------------------------------------------------- tickets

@app.get("/api/health")
async def health() -> dict[str, Any]:
    return {"ok": True, "model": MODEL_NAME, "running": _run_lock.locked()}


@app.get("/api/tickets")
async def tickets() -> dict[str, Any]:
    """Every ticket with its status and a simple open/resolved flag."""
    data = await _mcp("list_tickets")
    for t in data["tickets"]:
        t["state"] = "resolved" if t["status"] == "resolved" else "open"
    return data


@app.post("/api/tickets/{ticket_id}/run")
async def run_ticket(ticket_id: int) -> dict[str, Any]:
    """Start the agent team on one ticket in the background; poll /api/runs/{run_id} or /api/events."""
    ticket = await _mcp("get_ticket", ticket_id=ticket_id)
    if not ticket.get("found"):
        raise HTTPException(404, f"No ticket {ticket_id}.")
    if _run_lock.locked():
        raise HTTPException(409, "A team run is already in progress. Wait for it to finish.")

    deps = TeamDeps()
    RUNS[deps.run_id] = {"run_id": deps.run_id, "ticket_id": ticket_id, "status": "running",
                         "started_at": _now(), "report": None, "error": None}
    task = (f"Handle ticket {ticket_id} only ({ticket['type']} from {ticket['requester']}). "
            "Do not work on any other ticket. Prepare (don't make) any payment or purchase it needs.")

    async def go() -> None:
        async with _run_lock:
            try:
                report, _ = await run_team(task, deps=deps, ticket_id=ticket_id)
                RUNS[deps.run_id].update(status="done", report=report.model_dump())
                await _close_ticket(ticket_id, report)
            except Exception as exc:  # surfaced to the board instead of crashing the server
                RUNS[deps.run_id].update(status="error", error=str(exc))
            RUNS[deps.run_id]["finished_at"] = _now()

    asyncio.create_task(go())
    return {"run_id": deps.run_id, "ticket_id": ticket_id, "status": "running"}


async def _close_ticket(ticket_id: int, report: Any) -> None:
    """When a run finishes, mark its ticket resolved (through MCP) and note anything still waiting on a human."""
    pending = [a for a in report.approvals_needed if a.ticket_id in (None, ticket_id)]
    note = "Agent team run finished."
    if pending:
        note += " Waiting on human sign-off: " + "; ".join(
            f"{a.kind} {a.ref}" + (f" ${a.amount:,.2f}" if a.amount else "") for a in pending)
    await call("update_ticket", ticket_id=ticket_id, status="resolved", note=note)


@app.get("/api/runs/{run_id}")
async def get_run(run_id: str) -> dict[str, Any]:
    if run_id not in RUNS:
        raise HTTPException(404, f"No run {run_id} since the server started.")
    return RUNS[run_id]


# ---------------------------------------------------------------- events

def _simplify(e: dict[str, Any]) -> list[dict[str, Any]]:
    """Turn raw audit entries into board-friendly events: who said what, which tool they used."""
    base = {"ts": e.get("ts"), "run_id": e.get("run_id"), "agent": e.get("agent") or e.get("from")}
    ev = e.get("event")
    if ev == "agent_step" and e.get("node") == "model_response":
        out = []
        for p in e.get("parts", []):
            if p["type"] == "text" and p.get("content"):
                out.append({**base, "type": "said", "text": p["content"]})
            elif p["type"] == "tool_call" and p["tool"] != "final_result":
                out.append({**base, "type": "tool_call", "tool": p["tool"], "args": p.get("args")})
        return out
    if ev == "mcp_call":
        return [{**base, "type": "tool_result", "tool": e["tool"], "args": e.get("args"), "result": e.get("result")}]
    if ev == "delegate":
        return [{**base, "type": "delegate", "to": e["to"], "text": e["task"]}]
    if ev == "agent_start":
        return [{**base, "type": "start", "text": e.get("task")}]
    if ev == "agent_done":
        out = e.get("output") or {}
        return [{**base, "type": "done", "text": out.get("summary") if isinstance(out, dict) else out, "output": out}]
    if ev in ("run_start", "run_end", "run_error", "agent_stopped", "reset", "approve", "reject"):
        return [{**base, "type": ev, "text": e.get("task") or e.get("error") or e.get("reason"),
                 "ticket_id": e.get("ticket_id"), "detail": {k: v for k, v in e.items() if k not in base}}]
    return []


@app.get("/api/events")
async def events(limit: int = Query(100, le=1000), run_id: str | None = None,
                 ticket_id: int | None = None) -> dict[str, Any]:
    """Most recent agent events (newest last): what each agent said and which tools it used."""
    raw = json.loads(AUDIT_PATH.read_text() or "[]") if AUDIT_PATH.exists() else []
    if ticket_id is not None:
        run_ids = {e["run_id"] for e in raw if e.get("event") == "run_start" and e.get("ticket_id") == ticket_id}
        raw = [e for e in raw if e.get("run_id") in run_ids]
    if run_id:
        raw = [e for e in raw if e.get("run_id") == run_id]
    simple = [s for e in raw for s in _simplify(e)]
    return {"count": len(simple[-limit:]), "events": simple[-limit:]}


# ---------------------------------------------------------------- money

class ApproveBody(BaseModel):
    action_id: int
    approved_by: str  # maker
    checked_by: str   # checker (a different person)


class RejectBody(BaseModel):
    action_id: int
    rejected_by: str
    reason: str = ""


@app.get("/api/actions")
async def actions(status: str = "pending") -> dict[str, Any]:
    """Payments and purchases the agents prepared (pending / approved / rejected / failed / all)."""
    return await _mcp("list_pending_actions", status=status)


@app.post("/api/approve")
async def approve(body: ApproveBody) -> dict[str, Any]:
    """Human clicked approve: make the payment (changes cash) or place the purchase. Maker-checker."""
    result = await _mcp("approve_action", action_id=body.action_id,
                        approved_by=body.approved_by, checked_by=body.checked_by)
    audit.append({"run_id": None, "event": "approve", "agent": "human", **body.model_dump(), "result": result})
    if not result.get("ok"):
        raise HTTPException(400, result.get("error", "Approval failed."))
    return result


@app.post("/api/reject")
async def reject(body: RejectBody) -> dict[str, Any]:
    result = await _mcp("reject_action", action_id=body.action_id, rejected_by=body.rejected_by, reason=body.reason)
    audit.append({"run_id": None, "event": "reject", "agent": "human", **body.model_dump(), "result": result})
    if not result.get("ok"):
        raise HTTPException(400, result.get("error", "Reject failed."))
    return result


@app.get("/api/cash")
async def cash() -> dict[str, Any]:
    """Current checking balance from cash_accounts."""
    return await _mcp("get_cash_balance", account="checking")


# ---------------------------------------------------------------- reset

@app.post("/api/reset")
async def reset() -> dict[str, Any]:
    """Copy the original database over the working copy for a fresh run. The audit trail is kept."""
    if _run_lock.locked():
        raise HTTPException(409, "Can't reset while a team run is in progress.")
    shutil.copyfile(ORIGINAL_DB, WORKING_DB)
    audit.append({"run_id": None, "event": "reset", "agent": "human", "reason": "database reset to original"})
    return {"ok": True, "message": "data/campus_customs_new.db reset to the original values.",
            "cash": await _mcp("get_cash_balance", account="checking")}
