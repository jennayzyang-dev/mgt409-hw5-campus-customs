"""Inventory: stock levels, sizes, aisle locations, and reorders from vendors."""

from backend.agents.roles import SHARED_TOOLS, RoleSpec, register

SPEC = register(RoleSpec(
    name="inventory",
    title="Inventory Lead",
    job="checks stock by sku and size, finds alternatives, knows reprint/reorder status and vendor lead times, and prepares restock purchases for human approval",
    mcp_tools=SHARED_TOOLS + ("check_inventory", "list_inventory", "list_vendors", "get_invoice",
                              "prepare_purchase", "list_pending_actions"),
))
