"""Boss: triages open tickets, delegates, and reports to the human owner."""

from backend.agents.roles import SHARED_TOOLS, BossReport, RoleSpec, register

SPEC = register(RoleSpec(
    name="boss",
    title="Store Manager",
    job="triages every open ticket, assigns work, and writes the final report for the owner",
    mcp_tools=SHARED_TOOLS + ("get_cash_balance", "list_payments", "list_pending_actions", "update_ticket"),
    output_type=BossReport,
))
