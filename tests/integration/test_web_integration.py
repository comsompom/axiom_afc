from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from tests.bootstrap import SRC  # noqa: F401
from axiom.utils.activity_store import append_activity
from axiom.web.app import create_app


class WebIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._old = dict(os.environ)
        self._tmp = tempfile.TemporaryDirectory()
        self.activity_path = str(Path(self._tmp.name) / "activity_log.jsonl")
        os.environ["WALLET_MODE"] = "mock"
        os.environ["DEFAULT_USDT_TOKEN"] = "USDT"
        os.environ["CHECKING_WALLET_ADDRESS"] = "0xCheckingWallet"
        os.environ["TREASURY_WALLET_ADDRESS"] = "0xTreasuryWallet"
        os.environ["ALLOWED_CHAINS"] = "polygon,bnb"
        os.environ["APY_API_URL"] = ""
        os.environ["GAS_API_URL"] = ""
        os.environ["GITHUB_REPO_OWNER"] = ""
        os.environ["GITHUB_REPO_NAME"] = ""
        os.environ["ACTIVITY_LOG_PATH"] = self.activity_path
        append_activity(self.activity_path, "cycle_start", "ok", {"mandate": "test"})
        self.app = create_app()
        self.client = self.app.test_client()

    def tearDown(self) -> None:
        self._tmp.cleanup()
        os.environ.clear()
        os.environ.update(self._old)

    def test_home_menu_renders(self) -> None:
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Axiom Web Console", resp.data)
        self.assertIn(b"/dashboard", resp.data)

    def test_dashboard_renders(self) -> None:
        resp = self.client.get("/dashboard")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Axiom Dashboard", resp.data)

    def test_status_api_returns_expected_shape(self) -> None:
        resp = self.client.get("/api/status")
        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json()
        self.assertIn("wallet_mode", payload)
        self.assertIn("chain_quotes", payload)
        self.assertIn("checking_balance", payload)

    def test_activity_page_and_api(self) -> None:
        page = self.client.get("/activity")
        self.assertEqual(page.status_code, 200)
        self.assertIn(b"Axiom Activity", page.data)
        self.assertIn(b"Errors Only", page.data)

        api = self.client.get("/api/activity")
        self.assertEqual(api.status_code, 200)
        payload = api.get_json()
        self.assertIn("items", payload)
        self.assertGreaterEqual(len(payload["items"]), 1)
        self.assertIn("refreshed_at_utc", payload)

    def test_activity_api_filters(self) -> None:
        append_activity(self.activity_path, "yield_move", "skipped", {"reason": "disabled"})
        resp = self.client.get("/api/activity?action=yield_move&status=skipped&limit=10")
        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json()
        self.assertEqual(payload["filters"]["action"], "yield_move")
        self.assertEqual(payload["filters"]["status"], "skipped")
        self.assertGreaterEqual(payload["count"], 1)
        self.assertTrue(all(item["action"] == "yield_move" for item in payload["items"]))


if __name__ == "__main__":
    unittest.main()
