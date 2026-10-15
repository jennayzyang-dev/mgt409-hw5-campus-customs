"""Portkey / model configuration and run budgets. Every agent uses gpt-6-luna."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import UsageLimits

BACKEND = Path(__file__).resolve().parent
ROOT = BACKEND.parent
# project folder, then parent folders (first value found wins)
for env_dir in (BACKEND, ROOT, ROOT.parent, ROOT.parent.parent):
    load_dotenv(env_dir / ".env")

MODEL_NAME = "gpt-6-luna"  # fixed by the assignment; not overridable
PORTKEY_BASE_URL = os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1")
PROMPTS_DIR = BACKEND / "prompts"
MCP_SERVER = ROOT / "mcp_server" / "server.py"
AUDIT_PATH = ROOT / "output" / "audit_trail.json"

# token / cost budgets for one whole team run (shared across every delegation)
RUN_LIMITS = UsageLimits(request_limit=40, tool_calls_limit=60, total_tokens_limit=200_000)
MAX_DELEGATION_DEPTH = 3  # boss -> specialist -> specialist -> specialist, no deeper
MAX_DELEGATIONS_PER_RUN = 12
AUDIT_TEXT_LIMIT = 2000  # characters kept per text/tool result in the audit trail


def require_api_key() -> str:
    key = (os.getenv("PORTKEY_API_KEY") or os.getenv("portkey_api_key") or "").strip()
    if not key:
        raise RuntimeError("PORTKEY_API_KEY is missing. Add it to a .env in this project or a parent folder.")
    return key


@lru_cache(maxsize=1)
def build_model() -> OpenAIResponsesModel:
    client = AsyncOpenAI(
        api_key="unused",
        base_url=PORTKEY_BASE_URL,
        default_headers={"x-portkey-api-key": require_api_key()},
        timeout=60,
        max_retries=2,
    )
    return OpenAIResponsesModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))


def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8").strip()
