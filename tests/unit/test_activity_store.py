from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.bootstrap import SRC  # noqa: F401
from axiom.utils.activity_store import append_activity, filter_activities, read_recent_activities


class ActivityStoreTests(unittest.TestCase):
    def test_append_and_read_recent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "activity.jsonl")
            append_activity(path, "cycle_start", "ok", {"a": 1})
            append_activity(path, "payout_skip", "skipped", {"reason": "insufficient_balance"})
            rows = read_recent_activities(path, limit=10)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["action"], "payout_skip")
            self.assertEqual(rows[1]["action"], "cycle_start")

    def test_filter_activities_by_action_and_status(self) -> None:
        items = [
            {"action": "payout_transfer", "status": "ok"},
            {"action": "payout_transfer", "status": "error"},
            {"action": "yield_move", "status": "skipped"},
        ]
        by_action = filter_activities(items, action="payout_transfer")
        self.assertEqual(len(by_action), 2)
        by_status = filter_activities(items, status="skipped")
        self.assertEqual(len(by_status), 1)
        both = filter_activities(items, action="payout_transfer", status="error")
        self.assertEqual(len(both), 1)


if __name__ == "__main__":
    unittest.main()
