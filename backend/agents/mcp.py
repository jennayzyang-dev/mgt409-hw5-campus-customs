"""One MCP connection per agent to mcp_server/server.py, with money guardrails and audit logging.

All shop facts come from the MCP server. This wrapper only (1) hides tools a role
may not use, (2) never lets an agent call the human-only approve/reject tools and stamps
every prepared payment or purchase with the agent's name, and (3) writes every
MCP call to the audit trail. Money only moves through the dashboard's approve route.
"""

from __future__ import annotations

from typing import Any

from fastmcp.client import Client
from fastmcp.client.transports import PythonStdioTransport
from pydantic_ai import RunContext
from pydantic_ai.mcp import CallToolFunc, MCPToolset

from backend import audit
from backend.config import MCP_SERVER, ROOT
from backend.models import TeamDeps

HUMAN_ONLY = {"approve_action", "reject_action"}


def build_toolset(agent_name: str, allowed: tuple[str, ...]):
    async def guard_and_log(ctx: RunContext[TeamDeps], call_tool: CallToolFunc, name: str, args: dict[str, Any]):
        deps = ctx.deps
        if name in HUMAN_ONLY:
            result: Any = {"ok": False, "blocked": True, "error": "Only a human can approve or reject on the dashboard."}
            _log(deps, agent_name, name, args, result)
            return result
        if name in ("prepare_payment", "prepare_purchase"):
            args = {**args, "prepared_by": agent_name}  # the model can't claim someone else prepared it
        try:
            result = await call_tool(name, args)
        except Exception as exc:
            _log(deps, agent_name, name, args, {"error": str(exc)})
            raise
        _log(deps, agent_name, name, args, result)
        return result

    transport = PythonStdioTransport(MCP_SERVER, cwd=str(ROOT))
    toolset = MCPToolset(Client(transport), id=f"campus-customs-{agent_name}", process_tool_call=guard_and_log)
    return toolset.filtered(lambda ctx, tool_def: tool_def.name in allowed)


def _log(deps: TeamDeps, agent: str, tool: str, args: dict, result: Any) -> None:
    audit.append({"run_id": deps.run_id, "event": "mcp_call", "agent": agent, "depth": deps.depth,
                  "tool": tool, "args": args, "result": audit.clip(result)})
