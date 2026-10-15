# HW 5: Campus Customs Multi-Agent Operations

Five PydanticAI agents (boss, inventory, accounting, facilities, customer service) run a small Yale apparel shop on Chapel Street. They read and change shop data **only through a FastMCP server** over a SQLite database. A React desk lets a human pick a ticket, watch the agents work, and approve money moves with two signatures (maker-checker). Every agent uses `gpt-6-luna` through Portkey.

## 0. One-time setup

```bash
git clone <this repo> hw5 && cd hw5
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env            # then put your own PORTKEY_API_KEY in .env
cd frontend && npm install && cd ..
```

`.env` is git-ignored. The real key is never in this repo.

## 1. Copy the original database to the working copy (clean run)

`data/campus_customs.db` is the **original** and is never changed. `data/campus_customs_new.db` is the **working copy** that the agents, MCP server and routes update. Whenever you want a clean start, copy the original over the working copy:

```bash
cp data/campus_customs.db data/campus_customs_new.db
```

(The desk's **Reset day** button and `POST /api/reset` do the same copy.)

Both files are in this repo. The working copy is committed in its **final state from my Problem 9 run**: all 3 tickets resolved, invoice 501 paid, and checking at **$2,560.00**, which matches `output/desk_tickets.html` → Cash tab.

## 2. Start the MCP server

```bash
.venv/bin/python mcp_server/server.py
```

It runs over stdio and exposes 18 tools (see `mcp_server/README.md`). You usually don't need to start it by hand:
- **Vibe coder (Claude Code):** `.mcp.json` registers it as `campus-customs`. Open this folder in Claude Code from the project root and approve the server.
- **Agents and API routes:** the backend launches the same `server.py` over stdio automatically (`backend/agents/mcp.py`, `backend/mcp_client.py`).

## 3. Start the FastAPI backend

```bash
cd backend
../.venv/bin/uvicorn main:app --reload --port 8000
```

The backend runs at http://localhost:8000 (route list in `output/harness.md` → Backend Routes). If port 8000 is busy, stop whatever is using it first, because the board expects 8000.

## 4. Start the React board

In a second terminal:

```bash
cd frontend
npm run dev
```

This opens the desk at http://localhost:5173 (Vite uses 5174 if 5173 is busy, and the backend allows any local Vite port).

## 5. Reset the DB before a full three-ticket run

1. Click **Reset day** on the desk, or run `cp data/campus_customs.db data/campus_customs_new.db`. Checking should show **$3,400.00** and tickets 101, 102 and 103 should be open.
2. Click **Send to team →** on 101, wait until it's stamped RESOLVED, then do 102, then 103 (one run at a time).
3. Approve or reject slips in the **Sign-off tray**. Enter a maker and a *different* checker. Only approval moves cash.
4. The till should equal `cash_accounts` in `data/campus_customs_new.db`.

`output/audit_trail.json` is append-only. Every run adds to it and nothing deletes it.

## Where things are

| Problem | Files |
|---|---|
| 1. Prompt log | `AI_prompts.md` |
| 2. Database + harness | `data/`, `output/harness.md` |
| 3. MCP server | `mcp_server/server.py`, `mcp_server/README.md` |
| 4. Vibe coder connection + smoke test | `.mcp.json`, `output/mcp_smoke.json` |
| 5. Agent team | `backend/models.py`, `backend/prompts/`, `backend/agents/`, `output/audit_trail.json` |
| 6. Plan | `output/desk_tickets.html` (Expected sections) |
| 7. Backend routes | `backend/main.py` |
| 8. Dashboard | `frontend/`, `output/design.md` |
| 9. Resolve the tickets | `output/desk_tickets.html` (Actual + Cash tabs), `output/resolved_tickets.json`, `output/resolved_board.html` |
| 10. Reflection | `output/desk_tickets.html` (Reflection tab) |
| 11. Submission | `output/github_url.txt` |
