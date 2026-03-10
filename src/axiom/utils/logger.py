from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from axiom.utils.activity_store import append_activity


def log(message: str) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    print(f"[{ts}] {message}")


def log_action(
    action: str,
    status: str,
    details: dict[str, Any] | None = None,
    activity_log_path: str = "data/activity_log.jsonl",
) -> None:
    append_activity(activity_log_path, action=action, status=status, details=details)
