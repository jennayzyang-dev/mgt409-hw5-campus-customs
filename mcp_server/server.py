"""Campus Customs MCP server.

Exposes tools over data/campus_customs_new.db so every agent in HW 5 works
from the same source of truth. Tools only return what is in the database; if a
row is missing they say so instead of guessing. Agents can only *prepare*
payments and purchases (prepare_payment, prepare_purchase) and update tickets.
Money only moves through approve_action, which the dashboard's approve route
calls after two humans (maker + checker) click approve. The rules are enforced
here, on the server, so no agent prompt can talk its way around them.
"""

import calendar
import sqlite3
from datetime import date, timedelta
from pathlib import Path

from fastmcp import FastMCP

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "campus_customs_new.db"

mcp = FastMCP("campus-customs")


def _query(sql: str, params: tuple = ()) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        return [dict(row) for row in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


def _today() -> str:
    return _query("SELECT date_today FROM desk LIMIT 1")[0]["date_today"]


AGENT_NAMES = {"boss", "inventory", "accounting", "facilities", "customer_service",
               "customer service", "agent", "ai", "assistant", "system"}
TICKET_STATUSES = {"open", "in_progress", "waiting", "escalated", "resolved"}
RENT_WINDOW_DAYS = 7  # rent can only be paid when next_due is within this many days


@mcp.tool
def check_inventory(sku: str, size: str) -> dict:
    """Look up stock for one SKU in one size (qty on hand and aisle location).

    Use for customer orders, e.g. ticket 101 (CC-TEE-WHITE, size S).
    """
    rows = _query(
        "SELECT sku, name, size, qty, location FROM inventory WHERE sku = ? AND size = ?",
        (sku, size),
    )
    if not rows:
        return {"found": False, "sku": sku, "size": size,
                "message": "No inventory row for this sku/size."}
    return {"found": True, **rows[0]}


@mcp.tool
def get_lease(lease_id: int) -> dict:
    """Look up a lease: space, landlord, monthly rent, and next due date.

    Use for rent notices, e.g. ticket 102 (lease_id 1).
    """
    rows = _query(
        "SELECT id, space_name, landlord, monthly_rent, next_due, notes FROM leases WHERE id = ?",
        (lease_id,),
    )
    if not rows:
        return {"found": False, "lease_id": lease_id, "message": "No lease with this id."}
    return {"found": True, **rows[0]}


@mcp.tool
def get_pricing(sku: str) -> dict:
    """Look up unit cost and list price for a SKU, plus margin per unit.

    Use before answering discount requests, e.g. ticket 103 (CC-HOOD-NAVY).
    """
    rows = _query("SELECT sku, unit_cost, list_price FROM pricing WHERE sku = ?", (sku,))
    if not rows:
        return {"found": False, "sku": sku, "message": "No pricing row for this sku."}
    row = rows[0]
    row["margin_per_unit"] = round(row["list_price"] - row["unit_cost"], 2)
    return {"found": True, **row}



@mcp.tool
def list_inventory(sku: str) -> dict:
    """List stock for every size of one SKU.

    Use when the requested size is short and you need alternatives, e.g. ticket 103
    asks for 20 x CC-HOOD-NAVY size M.
    """
    rows = _query(
        "SELECT sku, name, size, qty, location FROM inventory WHERE sku = ? ORDER BY rowid", (sku,)
    )
    if not rows:
        return {"found": False, "sku": sku, "message": "No inventory rows for this sku."}
    return {"found": True, "sku": sku, "sizes": rows, "total_qty": sum(r["qty"] for r in rows)}


@mcp.tool
def get_today() -> dict:
    """Return the shop's business date from the desk table. Use it for every due-date check."""
    rows = _query("SELECT date_today, notes FROM desk LIMIT 1")
    return {"found": bool(rows), **(rows[0] if rows else {})}


@mcp.tool
def list_tickets() -> dict:
    """List every ticket (open and resolved) with its status."""
    rows = _query("SELECT * FROM tickets ORDER BY id")
    return {"count": len(rows), "tickets": rows}


@mcp.tool
def list_open_tickets() -> dict:
    """List every ticket that is not resolved, oldest first."""
    rows = _query("SELECT * FROM tickets WHERE status != 'resolved' ORDER BY created_at")
    return {"count": len(rows), "tickets": rows}


@mcp.tool
def get_ticket(ticket_id: int) -> dict:
    """Return one ticket with all its fields (type, requester, sku/size/qty, linked lease or invoice)."""
    rows = _query("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    if not rows:
        return {"found": False, "ticket_id": ticket_id, "message": "No ticket with this id."}
    return {"found": True, **rows[0]}


@mcp.tool
def get_invoice(invoice_id: int) -> dict:
    """Return a vendor invoice joined with its vendor, plus days overdue versus the desk date.

    Use for ticket 101, which is linked to invoice 501 (the rush reprint of the size S tee).
    """
    rows = _query(
        "SELECT i.id, i.vendor_id, v.name AS vendor_name, v.lead_days, i.amount, i.due_date, "
        "i.status, i.description FROM invoices i LEFT JOIN vendors v ON v.id = i.vendor_id "
        "WHERE i.id = ?",
        (invoice_id,),
    )
    if not rows:
        return {"found": False, "invoice_id": invoice_id, "message": "No invoice with this id."}
    row = rows[0]
    row["days_overdue"] = max(0, (date.fromisoformat(_today()) - date.fromisoformat(row["due_date"])).days)
    return {"found": True, **row}


@mcp.tool
def list_vendors() -> dict:
    """List every vendor with its specialty and lead time in days (who to reorder from, how long it takes)."""
    return {"vendors": _query("SELECT id, name, specialty, lead_days FROM vendors ORDER BY id")}


@mcp.tool
def get_cash_balance(account: str = "checking") -> dict:
    """Return the balance of one cash account. Check it before proposing or recording any payment."""
    rows = _query("SELECT name, balance, date FROM cash_accounts WHERE name = ?", (account,))
    if not rows:
        return {"found": False, "account": account, "message": "No cash account with this name."}
    return {"found": True, **rows[0]}


@mcp.tool
def list_payments() -> dict:
    """List every payment already recorded, so nothing is paid twice."""
    rows = _query("SELECT * FROM payments ORDER BY id")
    return {"count": len(rows), "payments": rows}


PENDING_SCHEMA = """
CREATE TABLE IF NOT EXISTS pending_actions (
    id INTEGER PRIMARY KEY,
    kind TEXT NOT NULL,            -- 'invoice' / 'rent' (payments) or 'purchase' (reorder)
    ref_id INTEGER,                -- invoices.id / leases.id for payments, vendors.id for purchases
    sku TEXT, size TEXT, qty INTEGER,
    amount REAL NOT NULL,
    ticket_id INTEGER,
    reason TEXT NOT NULL,
    prepared_by TEXT NOT NULL,     -- the agent that prepared it
    status TEXT NOT NULL,          -- pending / approved / rejected / failed
    created_at TEXT NOT NULL,
    decided_by TEXT, decided_at TEXT, result TEXT
)"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(PENDING_SCHEMA)
    return conn


def _amount_owed(conn: sqlite3.Connection, kind: str, ref_id: int) -> tuple[float | None, str | None]:
    """What is owed for an open invoice or due rent, or an error saying why it can't be paid."""
    today = conn.execute("SELECT date_today FROM desk LIMIT 1").fetchone()["date_today"]
    if kind == "invoice":
        inv = conn.execute("SELECT amount, status FROM invoices WHERE id = ?", (ref_id,)).fetchone()
        if inv is None:
            return None, f"No invoice {ref_id}."
        if inv["status"] != "open":
            return None, f"Invoice {ref_id} is {inv['status']}, not open."
        return inv["amount"], None
    if kind == "rent":
        lease = conn.execute("SELECT monthly_rent, next_due FROM leases WHERE id = ?", (ref_id,)).fetchone()
        if lease is None:
            return None, f"No lease {ref_id}."
        if (date.fromisoformat(lease["next_due"]) - date.fromisoformat(today)).days > RENT_WINDOW_DAYS:
            return None, f"Rent for lease {ref_id} is not due until {lease['next_due']}."
        return lease["monthly_rent"], None
    return None, "kind must be 'invoice' or 'rent'."


def _has_pending(conn: sqlite3.Connection, kind: str, ref_id: int, sku=None, size=None) -> int | None:
    row = conn.execute(
        "SELECT id FROM pending_actions WHERE status = 'pending' AND kind = ? AND ref_id = ? "
        "AND IFNULL(sku,'') = IFNULL(?,'') AND IFNULL(size,'') = IFNULL(?,'')",
        (kind, ref_id, sku, size),
    ).fetchone()
    return row["id"] if row else None


@mcp.tool
def prepare_payment(kind: str, ref_id: int, amount: float, reason: str, ticket_id: int | None = None,
                    prepared_by: str = "agent") -> dict:
    """Prepare (do NOT make) a payment for a human to approve on the dashboard.

    kind is "invoice" (ref_id = invoices.id) or "rent" (ref_id = leases.id). The amount must
    equal exactly what is owed. Nothing moves until two humans approve it (maker-checker).
    """
    conn = _connect()
    try:
        owed, err = _amount_owed(conn, kind, ref_id)
        if err:
            return {"ok": False, "error": err}
        if round(amount, 2) != round(owed, 2):
            return {"ok": False, "error": f"Amount {amount} does not match the {owed} owed."}
        existing = _has_pending(conn, kind, ref_id)
        if existing:
            return {"ok": True, "already_pending": True, "action_id": existing}
        cur = conn.execute(
            "INSERT INTO pending_actions (kind, ref_id, amount, ticket_id, reason, prepared_by, status, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)",
            (kind, ref_id, owed, ticket_id, reason.strip(), prepared_by, _today_conn(conn)),
        )
        conn.commit()
        return {"ok": True, "action_id": cur.lastrowid, "kind": kind, "ref_id": ref_id, "amount": owed,
                "status": "pending", "message": "Waiting for maker + checker approval on the dashboard."}
    finally:
        conn.close()


@mcp.tool
def prepare_purchase(vendor_id: int, sku: str, size: str, qty: int, reason: str, ticket_id: int | None = None,
                     prepared_by: str = "agent") -> dict:
    """Prepare (do NOT place) a restock order from a vendor for a human to approve.

    The cost is qty x unit_cost from the pricing table. Approving it creates an open vendor
    invoice; it does not spend cash until that invoice is paid.
    """
    if qty <= 0:
        return {"ok": False, "error": "qty must be positive."}
    conn = _connect()
    try:
        vendor = conn.execute("SELECT name, lead_days FROM vendors WHERE id = ?", (vendor_id,)).fetchone()
        if vendor is None:
            return {"ok": False, "error": f"No vendor {vendor_id}."}
        price = conn.execute("SELECT unit_cost FROM pricing WHERE sku = ?", (sku,)).fetchone()
        if price is None:
            return {"ok": False, "error": f"No pricing for {sku}."}
        if conn.execute("SELECT 1 FROM inventory WHERE sku = ? AND size = ?", (sku, size)).fetchone() is None:
            return {"ok": False, "error": f"{sku} has no size {size}."}
        existing = _has_pending(conn, "purchase", vendor_id, sku, size)
        if existing:
            return {"ok": True, "already_pending": True, "action_id": existing}
        amount = round(qty * price["unit_cost"], 2)
        cur = conn.execute(
            "INSERT INTO pending_actions (kind, ref_id, sku, size, qty, amount, ticket_id, reason, prepared_by, "
            "status, created_at) VALUES ('purchase', ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)",
            (vendor_id, sku, size, qty, amount, ticket_id, reason.strip(), prepared_by, _today_conn(conn)),
        )
        conn.commit()
        return {"ok": True, "action_id": cur.lastrowid, "vendor": vendor["name"], "lead_days": vendor["lead_days"],
                "sku": sku, "size": size, "qty": qty, "amount": amount, "status": "pending"}
    finally:
        conn.close()


@mcp.tool
def list_pending_actions(status: str = "pending") -> dict:
    """List payments and purchases prepared by agents, by status (pending/approved/rejected/failed/all)."""
    conn = _connect()
    try:
        sql, params = "SELECT * FROM pending_actions", ()
        if status != "all":
            sql, params = sql + " WHERE status = ?", (status,)
        rows = [dict(r) for r in conn.execute(sql + " ORDER BY id", params).fetchall()]
        return {"count": len(rows), "actions": rows}
    finally:
        conn.close()


@mcp.tool
def approve_action(action_id: int, approved_by: str, checked_by: str, account: str = "checking") -> dict:
    """HUMAN ONLY (called by the dashboard's approve route, never by an agent).

    Maker-checker: approved_by and checked_by must be two different named humans. A payment
    re-checks the amount owed and the balance, inserts a payments row, lowers cash, and marks
    the invoice paid or moves rent forward a month. A purchase creates an open vendor invoice.
    """
    maker, checker = (approved_by or "").strip(), (checked_by or "").strip()
    for role, person in (("approved_by (maker)", maker), ("checked_by (checker)", checker)):
        if not person or person.lower() in AGENT_NAMES:
            return {"ok": False, "error": f"{role} must be a named human."}
    if maker.lower() == checker.lower():
        return {"ok": False, "error": "Maker and checker must be two different people."}
    signed = f"{maker} (maker); {checker} (checker)"

    conn = _connect()
    try:
        action = conn.execute("SELECT * FROM pending_actions WHERE id = ?", (action_id,)).fetchone()
        if action is None:
            return {"ok": False, "error": f"No pending action {action_id}."}
        if action["status"] != "pending":
            return {"ok": False, "error": f"Action {action_id} is already {action['status']}."}
        today = _today_conn(conn)

        def finish(status: str, result: dict) -> dict:
            conn.execute("UPDATE pending_actions SET status = ?, decided_by = ?, decided_at = ?, result = ? "
                         "WHERE id = ?", (status, signed, today, str(result), action_id))
            conn.commit()
            return result

        if action["kind"] == "purchase":
            vendor = conn.execute("SELECT name, lead_days FROM vendors WHERE id = ?", (action["ref_id"],)).fetchone()
            due = date.fromisoformat(today) + timedelta(days=30)
            cur = conn.execute(
                "INSERT INTO invoices (vendor_id, amount, due_date, status, description) VALUES (?, ?, ?, 'open', ?)",
                (action["ref_id"], action["amount"], due.isoformat(),
                 f"Restock {action['qty']} x {action['sku']} {action['size']} (action {action_id})"),
            )
            return finish("approved", {"ok": True, "action_id": action_id, "kind": "purchase",
                                       "invoice_id": cur.lastrowid, "vendor": vendor["name"],
                                       "amount": action["amount"], "approved_by": signed,
                                       "expected_arrival": (date.fromisoformat(today)
                                                            + timedelta(days=vendor["lead_days"])).isoformat()})

        kind, ref_id, amount = action["kind"], action["ref_id"], action["amount"]
        owed, err = _amount_owed(conn, kind, ref_id)
        cash = conn.execute("SELECT balance FROM cash_accounts WHERE name = ?", (account,)).fetchone()
        if err or round(owed, 2) != round(amount, 2):
            return finish("failed", {"ok": False, "error": err or f"Amount owed changed to {owed}."})
        if cash is None or cash["balance"] < amount:
            return {"ok": False, "error": f"{account} balance does not cover {amount}; still pending."}

        cur = conn.execute(
            "INSERT INTO payments (kind, ref_id, amount, account, paid_at, approved_by) VALUES (?, ?, ?, ?, ?, ?)",
            (kind, ref_id, amount, account, today, signed),
        )
        conn.execute("UPDATE cash_accounts SET balance = balance - ?, date = ? WHERE name = ?", (amount, today, account))
        if kind == "invoice":
            conn.execute("UPDATE invoices SET status = 'paid' WHERE id = ?", (ref_id,))
        else:
            due = date.fromisoformat(conn.execute("SELECT next_due FROM leases WHERE id = ?", (ref_id,)).fetchone()[0])
            y, m = (due.year + due.month // 12, due.month % 12 + 1)
            nxt = due.replace(year=y, month=m, day=min(due.day, calendar.monthrange(y, m)[1]))
            conn.execute("UPDATE leases SET next_due = ? WHERE id = ?", (nxt.isoformat(), ref_id))
        new_balance = conn.execute("SELECT balance FROM cash_accounts WHERE name = ?", (account,)).fetchone()[0]
        return finish("approved", {"ok": True, "action_id": action_id, "kind": kind, "ref_id": ref_id,
                                   "payment_id": cur.lastrowid, "amount": amount, "paid_at": today,
                                   "approved_by": signed, "new_balance": new_balance})
    finally:
        conn.close()


@mcp.tool
def reject_action(action_id: int, rejected_by: str, reason: str = "") -> dict:
    """HUMAN ONLY. Reject a prepared payment or purchase; nothing is paid or ordered."""
    person = (rejected_by or "").strip()
    if not person or person.lower() in AGENT_NAMES:
        return {"ok": False, "error": "rejected_by must be a named human."}
    conn = _connect()
    try:
        action = conn.execute("SELECT status FROM pending_actions WHERE id = ?", (action_id,)).fetchone()
        if action is None or action["status"] != "pending":
            return {"ok": False, "error": f"Action {action_id} is not pending."}
        conn.execute("UPDATE pending_actions SET status = 'rejected', decided_by = ?, decided_at = ?, result = ? "
                     "WHERE id = ?", (person, _today_conn(conn), reason, action_id))
        conn.commit()
        return {"ok": True, "action_id": action_id, "status": "rejected"}
    finally:
        conn.close()


def _today_conn(conn: sqlite3.Connection) -> str:
    return conn.execute("SELECT date_today FROM desk LIMIT 1").fetchone()[0]


@mcp.tool
def update_ticket(ticket_id: int, status: str, note: str) -> dict:
    """Change a ticket's status and append a dated note (the old notes are kept).

    status must be one of: open, in_progress, waiting, escalated, resolved.
    """
    if status not in TICKET_STATUSES:
        return {"ok": False, "error": f"status must be one of {sorted(TICKET_STATUSES)}."}
    if not note.strip():
        return {"ok": False, "error": "A note explaining the change is required."}
    rows = _query("SELECT notes FROM tickets WHERE id = ?", (ticket_id,))
    if not rows:
        return {"ok": False, "error": f"No ticket {ticket_id}."}
    notes = (rows[0]["notes"] or "") + f"\n[{_today()}] {status}: {note.strip()}"
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("UPDATE tickets SET status = ?, notes = ? WHERE id = ?", (status, notes.strip(), ticket_id))
        conn.commit()
    finally:
        conn.close()
    return {"ok": True, "ticket_id": ticket_id, "status": status, "notes": notes.strip()}


if __name__ == "__main__":
    mcp.run(show_banner=False)
