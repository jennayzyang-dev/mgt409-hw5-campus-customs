# Campus Customs Agent Harness

How the whole system fits together. A human picks a ticket on the **React desk** (`frontend/`). The desk calls the **FastAPI routes** (`backend/main.py`), which start the **five PydanticAI agents** (`backend/agents/`). Agents read and change shop data only through the **MCP server** (`mcp_server/server.py`) over the **working database**. Every step is appended to `output/audit_trail.json`. Agents only *prepare* money moves, and two humans approve them on the desk.

| Part | Where | Section below |
|---|---|---|
| Tables | `data/campus_customs_new.db` (working copy of `data/campus_customs.db`) | Tables |
| MCP tools | `mcp_server/server.py` (also in `.mcp.json` for the vibe coder) | MCP Tools |
| Five agents | `backend/agents/`, `backend/prompts/`, `backend/models.py` | Agent Team |
| API routes | `backend/main.py`, run with `uvicorn main:app --reload --port 8000` from `backend/` | Backend Routes |
| Dashboard | `frontend/`, run with `npm run dev` | Dashboard |
| Safety rules | prompts + MCP server + routes | Safety |

Working database: `data/campus_customs_new.db` (copy of `data/campus_customs.db`). The agents' `prepare_*` tools add one extra table, `pending_actions` (id, kind, ref_id, sku, size, qty, amount, ticket_id, reason, prepared_by, status, created_at, decided_by, decided_at, result). It holds the payments and purchases waiting for human sign-off. `POST /api/reset` removes it with the rest of the working copy.

## Tables

### desk
- **Fields:** date_today, notes
- **Why it matters:** Check today's date so agents know what's due or overdue.

### tickets
- **Fields:** id, type, requester, subject, sku, size, qty, lease_id, invoice_id, status, notes, created_at
- **Why it matters:** The incoming requests (customers, landlord, student orgs) with item, size, qty, status, notes and created time, which tell agents what work to do.

### inventory
- **Fields:** sku, name, size, qty, location (primary key: sku + size)
- **Why it matters:** Stock by size, qty and location, so agents can check if an order can be filled and where to find it.

### pricing
- **Fields:** sku, unit_cost, list_price
- **Why it matters:** Unit cost and list price for each product, so agents can check margin before giving a discount.

### vendors
- **Fields:** id, name, specialty, lead_days
- **Why it matters:** Who each vendor is, their specialty and lead days, so agents know who to reorder from and how long it takes.

### leases
- **Fields:** id, space_name, landlord, monthly_rent, next_due, notes
- **Why it matters:** Landlord, rent and due date, so agents know when rent must be paid.

### cash_accounts
- **Fields:** name, balance, date
- **Why it matters:** Latest checking balance, so we don't overspend.

### payments
- **Fields:** id, kind, ref_id, amount, account, paid_at, approved_by
- **Why it matters:** Records every payment with amount, account and who approved it, so payments are tracked and signed off.

### invoices
- **Fields:** id, vendor_id, amount, due_date, status, description
- **Why it matters:** Bills vendors sent us, with amount, status, due date and description, so agents know what we owe and what's overdue.

## MCP Tools: first three (Problem 3)

### check_inventory(sku, size)
- **Reads:** `inventory`
- **Unlocks:** Ticket 101 (Tauhid Zaman, 1 × CC-TEE-WHITE size S)
- **Why it's the right tool:** Before promising Tauhid a tee, the agent has to check stock for that exact SKU and size. The result is 0 on hand, so the order can't be filled from the shelf and is waiting on the reprint in invoice 501.

### get_lease(lease_id)
- **Reads:** `leases`
- **Unlocks:** Ticket 102 (Elm City Properties rent notice, lease_id 1)
- **Why it's the right tool:** The rent email only says "due in 2 days," so the agent has to confirm the real amount ($2,400) and due date (2026-09-02) from the lease instead of trusting the email.

### get_pricing(sku)
- **Reads:** `pricing`
- **Unlocks:** Ticket 103 (Yale AI Club, 20 × CC-HOOD-NAVY size M, bulk discount request)
- **Why it's the right tool:** A discount can only be judged against cost. The hoodie costs $22 and lists at $58 ($36 margin per unit), so the agent knows how much room there is before offering any price.

## Agent Team

Built with PydanticAI in `backend/`. Every agent uses **gpt-6-luna** through Portkey (`backend/config.py`). Prompts are in `backend/prompts/<agent>.md`, data types in `backend/models.py`, and the role files in `backend/agents/`. Run it from the desk (one ticket per run) or from the command line with `.venv/bin/python -m backend.run`.

| Agent | Role file / prompt | Job | MCP tools it may call | Output |
|---|---|---|---|---|
| boss | `agents/boss.py`, `prompts/boss.md` | Triages open tickets, delegates, checks the whole cash picture, updates ticket status, reports to the owner | get_today, get_ticket, list_open_tickets, get_cash_balance, list_payments, list_pending_actions, update_ticket | BossReport |
| inventory | `agents/inventory.py`, `prompts/inventory.md` | Stock by sku + size, alternatives, reprint/reorder status, vendor lead times; prepares restock purchases | shared + check_inventory, list_inventory, list_vendors, get_invoice, prepare_purchase, list_pending_actions | AgentReport |
| accounting | `agents/accounting.py`, `prompts/accounting.md` | Cash, invoices, payments, pricing and margin; the **only** role that can prepare a payment | shared + get_cash_balance, list_payments, get_invoice, get_lease, get_pricing, list_vendors, prepare_payment, list_pending_actions | AgentReport |
| facilities | `agents/facilities.py`, `prompts/facilities.md` | The Chapel Street lease and landlord; checks rent notices against the lease | shared + get_lease, get_cash_balance, list_payments | AgentReport |
| customer_service | `agents/customer_service.py`, `prompts/customer_service.md` | Replies to customers and student groups; quotes list price only | shared + check_inventory, list_inventory, get_pricing, update_ticket | AgentReport |

"Shared" = get_today, get_ticket, list_open_tickets.

**Delegation (full connectivity):** every agent has a `delegate(to, task)` tool that can reach any of the other four (`agents/base.py`). The delegated agent runs its own loop with the same run state and returns its report as the tool result.

**Agent loop and audit:** `run_agent` drives each agent with `agent.iter()` and appends one entry per loop step to `output/audit_trail.json`: user prompt, model request (tool returns), model response (tool calls with args, text, tokens), and end. It also logs `agent_start` / `agent_done`, every `delegate` (from, to, task, depth), and every `mcp_call` (agent, tool, args, result). Each entry has `ts`, `run_id`, `agent`, `depth` and `chain`. The file is only ever appended to, under a file lock.

## MCP Tools (all 18)

| Tool | Table(s) | Read / write | Main ticket |
|---|---|---|---|
| check_inventory(sku, size) | inventory | read | 101 |
| get_lease(lease_id) | leases | read | 102 |
| get_pricing(sku) | pricing | read | 103 |
| list_inventory(sku) | inventory | read | 103 (only 8 of 20 size M) |
| get_today() | desk | read | all (due dates) |
| list_open_tickets() | tickets | read | all |
| get_ticket(ticket_id) | tickets | read | all |
| get_invoice(invoice_id) | invoices, vendors, desk | read | 101 (invoice 501) |
| list_vendors() | vendors | read | 101, 103 (reorder lead times) |
| get_cash_balance(account) | cash_accounts | read | 101, 102 |
| list_payments() | payments | read | 101, 102 (no double pay) |
| list_tickets() | tickets | read | all (dashboard) |
| prepare_payment(kind, ref_id, amount, reason, ticket_id) | invoices, leases, desk → pending_actions | **write** (prepare only) | 101 (invoice 501), 102 (rent) |
| prepare_purchase(vendor_id, sku, size, qty, reason, ticket_id) | vendors, pricing, inventory → pending_actions | **write** (prepare only) | 103 (restock 12 × size M) |
| list_pending_actions(status) | pending_actions | read | 101, 102, 103 |
| approve_action(action_id, approved_by, checked_by) — **human only** | pending_actions, payments, cash_accounts, invoices, leases | **write** (moves cash) | dashboard approve button |
| reject_action(action_id, rejected_by, reason) — **human only** | pending_actions | **write** | dashboard reject button |
| update_ticket(ticket_id, status, note) | tickets, desk | **write** | all |

## Safety

**Guardrails for real customers and real money**
- **Agents prepare, humans approve (maker-checker).** Agents can only `prepare_payment` / `prepare_purchase`, which adds a *pending* row to a `pending_actions` table. Cash only changes when two different people approve it on the dashboard (`POST /api/approve` → `approve_action`): a maker who approves and a checker who confirms. One person alone can't move money. Agents are blocked from `approve_action` / `reject_action` in `agents/mcp.py`, and the server rejects agent names and the same person as both maker and checker. Both names are saved on the payment row.
- **The server checks the money rules, not just the prompts.** At prepare *and* at approve time, amounts must exactly match the invoice or rent, invoices must be open, rent must be due within 7 days, the balance must cover the payment, and paying marks the invoice paid or moves rent forward a month, so nothing is paid twice.
- **Least privilege.** Each agent only sees the MCP tools its job needs. Only accounting can prepare payments, only inventory can prepare purchases, nobody but a human can approve, and only boss and customer service can change tickets.
- **One source of truth.** Every shop fact comes from MCP over `campus_customs_new.db`. Prompts require each number to be traced to a tool, and say "missing" instead of guessing.
- **Discount limits.** Accounting may only call a discount "within policy" up to 10% off list and at least 2× unit cost. Anything else, and every actual price change, goes to the owner. Customer service quotes list price only.
- **Ticket text is data.** Every prompt treats notes and emails as requests to evaluate, never instructions (defense against prompt injection, e.g. a fake rent email).
- **No over-promising or leaking.** Customer replies promise only confirmed stock and never mention costs, margins, cash or vendor bills.
- **Audit everything.** Every step, delegation and MCP call is in an append-only audit trail, so a person can check who did what and why. Human approvals, rejections and resets from the desk are logged there too.
- **The browser can only reach the API from the local desk.** CORS allows only the local Vite page, the approve route re-checks every rule on the server, and only one team run happens at a time, so two runs can't spend the same cash.

**Limits that keep token use in check**
- One run-wide budget shared across all delegations: max 40 model requests, 60 tool calls, 200k total tokens (`RUN_LIMITS`). When it's hit, the agent stops and returns a partial report.
- Delegation depth max 3, max 12 delegations per run, no delegating to yourself or back up the current chain (stops loops).
- Cheapest model (gpt-6-luna) for every agent. Tool results are compact JSON, and audit text is clipped to 2,000 characters per entry.
- Model calls time out after 60 s with 2 retries. The boss prompt asks for one delegation per question and about 8 delegations in a normal run.

## Backend Routes

`backend/main.py` (FastAPI). Start from `backend/`: `uvicorn main:app --reload --port 8000` → http://localhost:8000. Routes read and change shop data through the MCP server.

- `GET /api/health`: server is up, model name, and whether a team run is in progress.
- `GET /api/tickets`: all tickets with their status and an `open` / `resolved` state.
- `POST /api/tickets/{ticket_id}/run`: starts the agent team on that one ticket in the background and returns a `run_id` (one run at a time).
- `GET /api/runs/{run_id}`: status of a run (`running` / `done` / `error`) and the boss's final report.
- `GET /api/events?limit=&run_id=&ticket_id=`: recent agent events from the audit trail: what each agent said, delegations, tool calls and tool results.
- `GET /api/actions?status=pending`: payments and purchases the agents prepared and that are waiting for a human.
- `POST /api/approve` `{action_id, approved_by, checked_by}`: a human clicked approve. With a maker and a different checker it makes the payment (**the only route that changes cash**) or places the purchase.
- `POST /api/reject` `{action_id, rejected_by, reason}`: a human rejects a prepared payment or purchase.
- `GET /api/cash`: current checking balance from `cash_accounts`.
- `POST /api/reset`: copies `data/campus_customs.db` over `campus_customs_new.db` for a fresh run (the audit trail is kept).

## Dashboard

`frontend/` is React + Vite + TypeScript. Start it with `npm run dev` from `frontend/` (http://localhost:5173, or 5174 if 5173 is busy). It calls the backend at `http://localhost:8000` (`frontend/.env`), and the backend's CORS only allows the local Vite page. Full design notes are in `output/design.md`.

- **Ticket spike (left):** the three tickets as receipts, each with a **Send to team →** button (`POST /api/tickets/{id}/run`). Resolved tickets get a red RESOLVED stamp, plus a "to sign" tag if a human approval is still waiting.
- **The floor (center):** the boss station wired to the four specialists. Each agent has its own color and monogram, shows a live status lamp, what it's doing, its latest words and the MCP tools it used. The board polls `GET /api/events` every 1.5 s during a run. Below the floor are the **shift report** (boss summary, the draft customer reply, one card per agent) and the **shift log**.
- **The till and sign-off tray (right):** the live checking balance (`GET /api/cash`) rolls down after a payment. Each prepared payment or purchase is a slip with Maker and Checker signature lines (`POST /api/approve` / `/api/reject`). Approve stays disabled until two different names are signed.
- **Reset day** (`POST /api/reset`) restores the working database for a fresh run.

## What the full run showed (Problem 9)

The run was reset to $3,400.00, then tickets 101, 102 and 103 were each run on the desk until resolved. A human approved only invoice 501, so cash ended at **$2,560.00** (matches `cash_accounts`). Details are in `output/desk_tickets.html` (Actual and Cash tabs), `output/resolved_tickets.json` and `output/resolved_board.html`.

| Ticket | Agents that worked | Delegations | Model requests | Prepared | Approved |
|---|---|---|---|---|---|
| 101 | boss, inventory, accounting, customer_service | 5 | 23 | payment action 1, invoice 501, $840 | ✅ by Jenna Yang (maker) + Test Checker (checker) |
| 102 | boss, facilities, accounting | 3 | 14 | payment action 2, rent lease 1, $2,400 | not approved (pending) |
| 103 | boss, accounting, inventory, customer_service | 7 | 28 | purchase action 3, 12 × size M hoodies, $264 | not approved (pending) |

What worked: each ticket only used the specialists it needed, and facilities was idle on 101 and 103. The pending-action check stopped a duplicate rent payment and a duplicate reprint order. Nothing moved cash without two humans.

**Gaps found, and the rules to tighten next:**
- **Discount quoted without a human.** On ticket 103, customer service's draft reply offered the $52.20 (10% off) price, because the boss read "within policy" as approved. Fix: customer service gets no discount numbers until a `discount` approval is signed. A real version would make discounts a prepared action like payments.
- **Specialists check back with each other a lot.** 103 used 7 delegations and 28 model requests. Fix: lower `MAX_DELEGATIONS_PER_RUN` for single-ticket runs, or let only the boss delegate to customer service.
- **The boss started 103 with pricing, not stock.** The plan said inventory first. The boss prompt could say: "for a price request on a quantity, check stock before pricing."
