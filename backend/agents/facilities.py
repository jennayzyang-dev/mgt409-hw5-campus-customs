"""Facilities: the Chapel Street lease, landlord, and rent schedule."""

from backend.agents.roles import SHARED_TOOLS, RoleSpec, register

SPEC = register(RoleSpec(
    name="facilities",
    title="Facilities Manager",
    job="owns the shop lease and landlord relationship; confirms rent amount and due date",
    mcp_tools=SHARED_TOOLS + ("get_lease", "get_cash_balance", "list_payments"),
))
