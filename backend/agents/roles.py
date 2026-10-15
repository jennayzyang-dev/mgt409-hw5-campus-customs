"""Who is on the team and which MCP tools each role may call.

Every role can delegate to every other role (full connectivity) through the
`delegate` tool added in base.py; this table only limits shop-data access.
"""

from __future__ import annotations

from dataclasses import dataclass

from backend.models import AgentName, AgentReport, BossReport

SHARED_TOOLS = ("get_today", "get_ticket", "list_open_tickets")


@dataclass(frozen=True)
class RoleSpec:
    name: AgentName
    title: str
    job: str  # one line, shown to the other agents when they choose who to delegate to
    mcp_tools: tuple[str, ...]
    output_type: type = AgentReport


ROLES: dict[str, RoleSpec] = {}


def register(spec: RoleSpec) -> RoleSpec:
    ROLES[spec.name] = spec
    return spec


def roster(excluding: str) -> str:
    return "\n".join(f"- {r.name}: {r.job}" for r in ROLES.values() if r.name != excluding)


__all__ = ["AgentReport", "BossReport", "ROLES", "RoleSpec", "SHARED_TOOLS", "register", "roster"]
