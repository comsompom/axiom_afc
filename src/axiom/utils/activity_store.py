from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def append_activity(path: str, action: str, status: str, details: dict[str, Any] | None = None) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "status": status,
        "details": details or {},
    }
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True) + "\n")


def read_recent_activities(path: str, limit: int = 50) -> list[dict[str, Any]]:
    target = Path(path)
    if not target.exists():
        return []
    lines = target.read_text(encoding="utf-8").splitlines()
    rows: list[dict[str, Any]] = []
    for raw in lines[-limit:]:
        raw = raw.strip()
        if not raw:
            continue
        try:
            rows.append(json.loads(raw))
        except json.JSONDecodeError:
            continue
    rows.reverse()
    return rows


def filter_activities(
    items: list[dict[str, Any]],
    action: str | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    filtered = items
    if action:
        action_lower = action.strip().lower()
        filtered = [row for row in filtered if str(row.get("action", "")).lower() == action_lower]
    if status:
        status_lower = status.strip().lower()
        filtered = [row for row in filtered if str(row.get("status", "")).lower() == status_lower]
    return filtered
