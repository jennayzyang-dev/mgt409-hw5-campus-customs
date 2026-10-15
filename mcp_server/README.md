# Campus Customs MCP Server

This is the shared toolbox for every agent in HW 5. Agents don't query the database directly. They call these tools, so they all read the same data and can't make anything up. If a row doesn't exist, the tool says so. Agents can only *prepare* payments and purchases; the dashboard's approve route is the only thing that moves cash.

**Database:** `data/campus_customs_new.db` (the working copy; the original `data/campus_customs.db` is never touched)

**Built with:** [FastMCP](https://gofastmcp.com), entry point `server.py`. It's registered for the vibe coder in `.mcp.json`, and the PydanticAI agents connect to it over stdio (`backend/agents/mcp.py`).

## Tools

| Tool | Reads / writes | What it does |
|---|---|---|
| `check_inventory(sku, size)` | inventory | Qty on hand and aisle for one SKU in one size |
| `list_inventory(sku)` | inventory | Every size of one SKU, plus total qty |
| `get_lease(lease_id)` | leases | Space, landlord, monthly rent, next due date |
| `get_pricing(sku)` | pricing | Unit cost, list price, margin per unit |
| `get_today()` | desk | The shop's business date |
| `list_open_tickets()` | tickets | Every ticket that isn't resolved |
| `get_ticket(ticket_id)` | tickets | One ticket with all its fields |
| `get_invoice(invoice_id)` | invoices, vendors | Invoice + vendor name/lead time + days overdue |
| `list_vendors()` | vendors | Vendors, specialty, lead days |
| `get_cash_balance(account)` | cash_accounts | Current balance of an account |
| `list_payments()` | payments | Payments already made |
| `list_tickets()` | tickets | Every ticket, open and resolved |
| `prepare_payment(kind, ref_id, amount, reason, ticket_id)` | **writes** pending_actions | Prepares (doesn't pay) an open invoice or due rent, exact amount only |
| `prepare_purchase(vendor_id, sku, size, qty, reason, ticket_id)` | **writes** pending_actions | Prepares (doesn't place) a restock; cost = qty × unit cost |
| `list_pending_actions(status)` | pending_actions | Prepared payments/purchases and their status |
| `approve_action(action_id, approved_by, checked_by)` | **writes** payments, cash_accounts, invoices / leases | **Human only** (dashboard approve route). Maker-checker: two different named people. Pays, or turns a purchase into a vendor invoice |
| `reject_action(action_id, rejected_by, reason)` | **writes** pending_actions | **Human only.** Rejects a prepared action |
| `update_ticket(ticket_id, status, note)` | **writes** tickets | Changes status and appends a dated note |
