from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests.bootstrap import SRC  # noqa: F401
from axiom.github.github_client import GithubClient


class GithubClientTests(unittest.TestCase):
    def test_mock_events_return_when_wallet_mapping_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mapping_path = Path(tmp) / "wallets.json"
            mapping_path.write_text(json.dumps({"demo-dev": "0xabc"}), encoding="utf-8")

            client = GithubClient(owner="", repo="", token="", contributor_wallets_path=str(mapping_path))
            events = client.recent_merged_prs()
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].payout_address, "0xabc")

    def test_mock_events_empty_when_mapping_missing(self) -> None:
        client = GithubClient(owner="", repo="", token="", contributor_wallets_path="missing.json")
        events = client.recent_merged_prs()
        self.assertEqual(events, [])


if __name__ == "__main__":
    unittest.main()
