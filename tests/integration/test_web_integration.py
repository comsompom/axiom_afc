from __future__ import annotations

import os
import unittest

from tests.bootstrap import SRC  # noqa: F401
from axiom.web.app import create_app


class WebIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._old = dict(os.environ)
        os.environ["WALLET_MODE"] = "mock"
        os.environ["DEFAULT_USDT_TOKEN"] = "USDT"
        os.environ["CHECKING_WALLET_ADDRESS"] = "0xCheckingWallet"
        os.environ["TREASURY_WALLET_ADDRESS"] = "0xTreasuryWallet"
        os.environ["ALLOWED_CHAINS"] = "polygon,bnb"
        os.environ["APY_API_URL"] = ""
        os.environ["GAS_API_URL"] = ""
        os.environ["GITHUB_REPO_OWNER"] = ""
        os.environ["GITHUB_REPO_NAME"] = ""
        self.app = create_app()
        self.client = self.app.test_client()

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._old)

    def test_dashboard_renders(self) -> None:
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Axiom Dashboard", resp.data)

    def test_status_api_returns_expected_shape(self) -> None:
        resp = self.client.get("/api/status")
        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json()
        self.assertIn("wallet_mode", payload)
        self.assertIn("chain_quotes", payload)
        self.assertIn("checking_balance", payload)


if __name__ == "__main__":
    unittest.main()
