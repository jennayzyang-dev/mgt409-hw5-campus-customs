"""Builds the five agents, runs each agent loop step by step, and wires delegation.

Every step of every agent loop (model request, model response with its tool calls,
final output) is appended to output/audit_trail.json.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from pydantic_ai import Agent, RunContext
from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.messages import (RetryPromptPart, TextPart, ThinkingPart, ToolCallPart,
                                  ToolReturnPart, UserPromptPart)
from pydantic_ai.usage import RunUsage

from backend import audit
from backend.agents import accounting, boss, customer_service, facilities, inventory  # noqa: F401 (registers roles)
from backend.agents.mcp import build_toolset
from backend.agents.roles import ROLES, roster
from backend.config import MAX_DELEGATION_DEPTH, MAX_DELEGATIONS_PER_RUN, RUN_LIMITS, build_model, load_prompt
from backend.models import AgentName, TeamDeps

_agents: dict[str, Agent] = {}


def get_agent(name: str) -> Agent:
    if name in _agents:
        return _agents[name]
    spec = ROLES[name]
    instructions = (
        load_prompt(name)
        + f"\n\n## Your teammates (use the delegate tool)\n{roster(excluding=name)}"
    )
    agent = Agent(
        build_model(),
        deps_type=TeamDeps,
        output_type=spec.output_type,
        instructions=instructions,
        toolsets=[build_toolset(name, spec.mcp_tools)],
        name=name,
        retries=1,
    )

    @agent.tool
    async def delegate(ctx: RunContext[TeamDeps], to: AgentName, task: str) -> dict[str, Any]:
        """Hand a focused task to a teammate and get their report back.

        Args:
            to: boss, inventory, accounting, facilities, or customer_service (not yourself).
            task: Self-contained instructions: the ticket id, the exact sku/size/qty or
                invoice/lease id, and what answer you need back.
        """
        deps = ctx.deps
        if to == name:
            return {"error": "You cannot delegate to yourself."}
        if to in deps.chain:
            return {"error": f"{to} is already working on this chain ({' -> '.join(deps.chain)}); "
                             "answer with what you have instead of sending it back."}
        if deps.depth + 1 > MAX_DELEGATION_DEPTH:
            return {"error": "Delegation depth limit reached. Finish with what you know and flag gaps."}
        if len(deps.delegations) >= MAX_DELEGATIONS_PER_RUN:
            return {"error": "Delegation budget for this run is used up. Finish with what you know."}
        deps.delegations.append({"from": name, "to": to, "task": task})
        audit.append({"run_id": deps.run_id, "event": "delegate", "from": name, "to": to,
                      "depth": deps.depth + 1, "task": task})
        child = replace(deps, depth=deps.depth + 1, chain=deps.chain + (name,))
        output = await run_agent(to, task, child, usage=ctx.usage)
        return output.model_dump() if hasattr(output, "model_dump") else {"reply": str(output)}

    _agents[name] = agent
    return agent


async def run_agent(name: str, task: str, deps: TeamDeps, usage: RunUsage | None = None):
    """Run one agent loop to completion, auditing every node."""
    agent = get_agent(name)
    base = {"run_id": deps.run_id, "agent": name, "depth": deps.depth, "chain": list(deps.chain)}
    audit.append({**base, "event": "agent_start", "task": task})
    step = 0
    try:
        async with agent.iter(task, deps=deps, usage=usage, usage_limits=RUN_LIMITS) as run:
            async for node in run:
                step += 1
                audit.append({**base, "event": "agent_step", "step": step, **_describe(node),
                              "usage_so_far": _usage(run.usage)})
            output = run.result.output
    except UsageLimitExceeded as exc:
        audit.append({**base, "event": "agent_stopped", "step": step, "reason": f"usage limit: {exc}"})
        return _fallback(name, f"Stopped early: run budget exceeded ({exc}). Partial work only.")
    audit.append({**base, "event": "agent_done", "steps": step, "output": output.model_dump()})  # kept whole for the board
    return output


async def run_team(task: str, deps: TeamDeps | None = None, ticket_id: int | None = None):
    """Start a team run at the boss and log run_start / run_end around it."""
    deps = deps or TeamDeps()
    audit.append({"run_id": deps.run_id, "event": "run_start", "task": task, "ticket_id": ticket_id})
    try:
        report = await run_agent("boss", task, deps)
    except Exception as exc:
        audit.append({"run_id": deps.run_id, "event": "run_error", "ticket_id": ticket_id, "error": str(exc)})
        raise
    audit.append({"run_id": deps.run_id, "event": "run_end", "ticket_id": ticket_id,
                  "delegations": len(deps.delegations), "output": report.model_dump()})
    return report, deps


def _fallback(name: str, message: str):
    spec = ROLES[name]
    if name == "boss":
        return spec.output_type(summary=message)
    return spec.output_type(agent=name, summary=message)


def _usage(u: RunUsage) -> dict[str, int]:
    return {"requests": u.requests, "input_tokens": u.input_tokens, "output_tokens": u.output_tokens,
            "tool_calls": u.tool_calls}


def _describe(node: Any) -> dict[str, Any]:
    """Turn one graph node into a compact, auditable record."""
    if Agent.is_user_prompt_node(node):
        return {"node": "user_prompt", "prompt": audit.clip(str(node.user_prompt))}
    if Agent.is_model_request_node(node):
        parts = []
        for p in node.request.parts:
            if isinstance(p, UserPromptPart):
                parts.append({"type": "user_prompt", "content": audit.clip(str(p.content))})
            elif isinstance(p, ToolReturnPart):
                parts.append({"type": "tool_return", "tool": p.tool_name, "content": audit.clip(p.content)})
            elif isinstance(p, RetryPromptPart):
                parts.append({"type": "retry", "tool": p.tool_name, "content": audit.clip(str(p.content))})
        return {"node": "model_request", "parts": parts}
    if Agent.is_call_tools_node(node):
        resp = node.model_response
        parts = []
        for p in resp.parts:
            if isinstance(p, ToolCallPart):
                parts.append({"type": "tool_call", "tool": p.tool_name, "args": p.args_as_dict()})
            elif isinstance(p, TextPart):
                parts.append({"type": "text", "content": audit.clip(p.content)})
            elif isinstance(p, ThinkingPart):
                parts.append({"type": "thinking", "chars": len(p.content or "")})
        return {"node": "model_response", "model": resp.model_name, "parts": parts,
                "tokens": {"input": resp.usage.input_tokens, "output": resp.usage.output_tokens}}
    if Agent.is_end_node(node):
        return {"node": "end"}
    return {"node": type(node).__name__}
