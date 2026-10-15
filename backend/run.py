"""Run the Campus Customs team from the command line.

    .venv/bin/python -m backend.run                      # all open tickets
    .venv/bin/python -m backend.run "Handle ticket 102 only"

Agents only prepare payments and purchases; a human approves them on the dashboard
(POST /api/approve), which is the only place cash changes.
"""

from __future__ import annotations

import argparse
import asyncio
import json

from backend.agents.base import run_team

DEFAULT_TASK = "Work every open ticket in the shop. Report what you did and what needs my approval."


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("task", nargs="?", default=DEFAULT_TASK)
    args = parser.parse_args()
    report, _ = await run_team(args.task)
    print(json.dumps(report.model_dump(), indent=2))


if __name__ == "__main__":
    asyncio.run(main())
