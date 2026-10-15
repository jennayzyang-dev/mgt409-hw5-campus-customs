"""Customer service: replies to customers and student groups, quotes list prices."""

from backend.agents.roles import SHARED_TOOLS, RoleSpec, register

SPEC = register(RoleSpec(
    name="customer_service",
    title="Customer Service Rep",
    job="talks to customers and student groups, checks what can be promised, and drafts replies",
    mcp_tools=SHARED_TOOLS + ("check_inventory", "list_inventory", "get_pricing", "update_ticket"),
))
