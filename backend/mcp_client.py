"""Call the Campus Customs MCP server from the API routes (same server the agents use)."""

from __future__ import annotations

from typing import Any

from fastmcp.client import Client
from fastmcp.client.transports import PythonStdioTransport

from backend.config import MCP_SERVER, ROOT


async def call(tool: str, **args: Any) -> Any:
    async with Client(PythonStdioTransport(MCP_SERVER, cwd=str(ROOT))) as client:
        result = await client.call_tool(tool, args, raise_on_error=True)
    return result.structured_content if result.structured_content is not None else result.data
