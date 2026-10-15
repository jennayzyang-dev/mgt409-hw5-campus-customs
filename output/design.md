# The Desk: dashboard design

The dashboard is `frontend/` (React + Vite + TypeScript). Start it with `npm run dev` from `frontend/` and it opens at http://localhost:5173. It talks to the FastAPI backend at http://localhost:8000 (`frontend/.env` → `VITE_API_URL`).

## The idea: a shop counter, not a SaaS admin panel

Campus Customs is a small apparel shop on Chapel Street, so the board is drawn like the **front desk of that shop**: a painted shop sign at the top, a kraft-paper desk surface, paper tickets on a spike, a cash register, and a tray of slips waiting for signatures. Every element is a physical object people already know how to read. Nobody needs a tutorial to know that a receipt on a spike is work to do, a red stamp means it's done, and a slip in the tray needs a signature. The goal is a desk you'd actually want to sit at during a shift, not a grid of gray cards.

## Layout (three zones, left to right = how work flows)

| Zone | What it is | Why |
|---|---|---|
| **Left: Ticket spike** | The 3 tickets as thermal-paper receipts with a pin hole, torn bottom edge, monospace type and a slight tilt | Incoming work lives on the left like an in-tray. Each receipt shows the ticket number, time, type, requester, item and the note, so you can triage without opening anything. Its **Send to team →** button starts the agents on that one ticket. |
| **Center: The floor** | The boss station on top, wired to the four specialist stations below | This is the "watch them work" area. You see the org chart and the activity at the same time. Under it are the **Shift report** (what each agent did) and the **Shift log** (every message and tool call, newest at the bottom). |
| **Right: The till + Sign-off tray** | A dark cash-register display with green LCD digits, and yellow carbon-copy slips | Money is kept separate on purpose, on its own side of the desk. The human's job (sign or reject) sits right under the balance it changes. |

On narrow screens the three zones stack into one column.

## How the agents read differently

Each agent has its own **ink color, monogram and station name**, used consistently on the floor, in the hand-off chips, the shift log, the shift report and the "prepared by" line on slips:

| Agent | Ink | Monogram | Station |
|---|---|---|---|
| Boss (Store Manager) | navy | B | Front desk |
| Inventory Lead | forest green | In | Stockroom |
| Bookkeeper (accounting) | ledger gold | Ac | Back office |
| Facilities | brick red | Fa | Chapel St. lease |
| Customer Service | plum | CS | Counter |

- **State is shown by light and weight, not only text.** An idle station is faded and says "Not called on this ticket", which makes the plan-vs-actual comparison (Problem 6) visible at a glance. A working station fills with its tint, gets an outline and a pulsing lamp, and shows what it's doing in plain English ("checked the shelf", "opened the lease") next to the raw MCP tool name in a chip. A done station shows a green lamp and "clocked out".
- **Speech bubbles** show the agent's latest words or the task it was handed, so you read the agents like people talking at the counter.
- **Hand-off wires:** the curved lines from the boss to each specialist are gray dashes when unused, turn solid once that agent is called, and animate (marching dashes) while the hand-off is live. Hand-off chips under the floor list every delegation in order, including specialist-to-specialist ones (e.g. Bookkeeper → Inventory Lead).
- **Tools used** stay on each station as small chips after the run, so the station doubles as a record of which MCP tools that agent touched.

## How resolved tickets show up

When a run finishes, the backend marks the ticket `resolved`. Its receipt gets a **red double-ruled RESOLVED rubber stamp** that "thunks" onto the paper (it scales down and settles at an angle, with multiply blend so it looks inked). The status pill turns green, the "Send to team" button goes away, and the open count in the header drops. If the agents left something for a human, the receipt also carries a yellow **"1 to sign"** pill, so resolved never hides money that is still waiting. A toast says the ticket is done and points you to the report and the tray.

The **Shift report** then shows the boss's summary in a larger serif (the "manager's note"), the **draft reply to the customer** on a yellow note card, and one card per agent that worked: what it did, who called it, and how many tool calls it made.

## How cash shows up

- **The till** is a dark register with glowing green tabular digits. It always shows the live checking balance from `/api/cash`.
- **After an approved payment the number rolls down** to the new balance (an eased counter animation), and a red **−$840.00** ticks under it and fades. You literally see the money leave the drawer, which makes approving feel as serious as it is.
- **A preview line** under the till shows what the balance would be if every waiting slip were signed, and turns amber when that drops under the shop's **$300** low-cash line (rent + invoice 501 would leave $160).
- **The sign-off tray** is the only place money moves. Each prepared payment or purchase is a yellow carbon slip (purchases are blue, because they create a vendor bill rather than spending cash) with the amount, ticket, which agent prepared it, and its reason. There are two signature lines, **Maker** and **Checker**, in a handwriting font. **Approve & pay** stays disabled until two *different* names are signed, which matches the backend's maker-checker rule. Signed slips drop into a small history with a green **PAID** / **ORDERED** or red **REJECTED** stamp.

## Small touches that make it feel alive

- The shop sign has a live status light: green "Shop is open", gold pulsing "Team is working", or red "Backend offline" with the exact command to start the server.
- The board polls every 1.5 s while agents work and every 6 s when idle, so it feels live without wasting requests.
- Receipts tilt slightly like real paper on a spike and straighten when you hover or select one.
- "Reset day" in the sign resets the database for a fresh run (with a confirm), and keeps the audit trail.
- Signer names are remembered in the browser so the people at the desk don't retype them every time.
- Colors are warm (kraft, cream, navy and gold, a nod to Yale blue), type mixes a book serif for headings and people, monospace for receipts and money, and a clean sans for the UI, so each kind of information has its own voice.
