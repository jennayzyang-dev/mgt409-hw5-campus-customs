"""Accounting: cash, invoices, payments, pricing and margin."""

from backend.agents.roles import SHARED_TOOLS, RoleSpec, register

SPEC = register(RoleSpec(
    name="accounting",
    title="Bookkeeper",
    job="owns cash, vendor invoices, payments and pricing/margin; the only role that prepares payments for human approval",
    mcp_tools=SHARED_TOOLS + ("get_cash_balance", "list_payments", "get_invoice", "get_lease",
                              "get_pricing", "list_vendors", "prepare_payment", "list_pending_actions"),
))
