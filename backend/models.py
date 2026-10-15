"""Data types shared by the Campus Customs agent team."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field

AgentName = Literal["boss", "inventory", "accounting", "facilities", "customer_service"]
AGENT_NAMES: tuple[AgentName, ...] = ("boss", "inventory", "accounting", "facilities", "customer_service")
TicketStatus = Literal["open", "in_progress", "waiting", "escalated", "resolved"]


class ApprovalRequest(BaseModel):
    """Something only a human owner can sign off on (money out, discounts, exceptions)."""

    kind: Literal["payment", "purchase", "discount", "refund", "exception"]
    action_id: int | None = Field(default=None, description="pending_actions id from prepare_payment/prepare_purchase")
    ticket_id: int | None = None
    ref: str = Field(description='What it applies to, e.g. "invoice:501", "rent:1", "sku:CC-HOOD-NAVY"')
    amount: float | None = None
    reason: str


class AgentReport(BaseModel):
    """What a specialist hands back to whoever delegated to it."""

    agent: AgentName
    summary: str
    ticket_ids: list[int] = []
    facts_used: list[str] = Field(default=[], description="Each fact with the MCP tool it came from")
    actions_taken: list[str] = Field(default=[], description="Writes actually made through MCP tools")
    needs_human: list[ApprovalRequest] = []


class TicketOutcome(BaseModel):
    ticket_id: int
    status: TicketStatus
    owner: AgentName
    resolution: str
    customer_reply: str | None = Field(default=None, description="Draft message to the requester, if any")


class BossReport(BaseModel):
    """The boss's final answer to the shop owner for one run."""

    summary: str
    tickets: list[TicketOutcome] = []
    approvals_needed: list[ApprovalRequest] = []
    cash_after_run: float | None = None


@dataclass
class TeamDeps:
    """State shared by every agent in one run (passed down through delegation)."""

    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    depth: int = 0
    chain: tuple[str, ...] = ()
    delegations: list[dict] = field(default_factory=list)  # shared list, counts across the whole run
