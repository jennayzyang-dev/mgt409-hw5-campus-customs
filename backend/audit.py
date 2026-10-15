"""Append-only audit trail at output/audit_trail.json (a JSON list; never wiped)."""

from __future__ import annotations

import fcntl
import json
import os
from datetime import datetime, timezone
from typing import Any

from backend.config import AUDIT_PATH, AUDIT_TEXT_LIMIT


def clip(value: Any) -> Any:
    text = value if isinstance(value, str) else json.dumps(value, default=str)
    if len(text) <= AUDIT_TEXT_LIMIT:
        return value
    return text[:AUDIT_TEXT_LIMIT] + f"... [clipped {len(text) - AUDIT_TEXT_LIMIT} chars]"


def append(entry: dict[str, Any]) -> None:
    """Add one entry to the audit list. Locks the file so parallel writes can't clobber it."""
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), **entry}
    lock_path = AUDIT_PATH.with_suffix(".lock")
    with open(lock_path, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        raw = AUDIT_PATH.read_text(encoding="utf-8").strip() if AUDIT_PATH.exists() else ""
        entries = json.loads(raw) if raw else []
        entries.append(entry)
        tmp = AUDIT_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(entries, indent=2, default=str), encoding="utf-8")
        os.replace(tmp, AUDIT_PATH)
