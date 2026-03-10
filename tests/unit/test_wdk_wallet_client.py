from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.bootstrap import SRC  # noqa: F401
from axiom.wallet.wdk_wallet_client import WdkWalletClient


class WdkWalletClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.token_map = root / "token_map.json"
        self.protocol_map = root / "protocol_map.json"
        self.token_map.write_text(
            json.dumps(
                {
                    "polygon": {
                        "USDT": {"address": "0xToken", "decimals": 6},
                        "BINOM": {"address": "0xBinom", "decimals": 6},
                    }
                }
            ),
            encoding="utf-8",
        )
        self.protocol_map.write_text(
            json.dumps(
                {
                    "lending": {"polygon": {"aave-v3": {"pool_address": "0xPool"}}},
                    "swap": {"polygon": {"USDT_to_BINOM": {"to_token_symbol": "BINOM"}}},
                }
            ),
            encoding="utf-8",
        )
        self.client = WdkWalletClient(
            module_name="wdk-http",
            token_map_path=str(self.token_map),
            protocol_map_path=str(self.protocol_map),
            allowed_chains=["polygon"],
            default_chain="polygon",
            wdk_service_url="http://localhost:8787",
            timeout_seconds=5,
            api_key="secret-key",
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_amount_conversions(self) -> None:
        units = self.client._to_base_units(1.234567, 6)  # noqa: SLF001
        self.assertEqual(units, 1234567)
        value = self.client._from_base_units("1234567", 6)  # noqa: SLF001
        self.assertAlmostEqual(value, 1.234567)

    def test_get_balance_uses_service_response(self) -> None:
        with patch.object(self.client, "_call_service", return_value={"ok": True, "balance": "4.2"}):
            bal = self.client.get_balance("0xMe", "USDT")
            self.assertEqual(bal, 4.2)

    def test_transfer_extracts_tx_hash(self) -> None:
        with patch.object(self.client, "_call_service", return_value={"ok": True, "tx_hash": "0x123"}):
            tx_hash = self.client.transfer("USDT", "0xFrom", "0xTo", 1.0, "polygon")
            self.assertEqual(tx_hash, "0x123")

    def test_call_service_includes_api_key_header(self) -> None:
        captured = {}

        class _Resp:
            def read(self):
                return b'{"ok": true, "balance": "1"}'

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        def _fake_urlopen(req, timeout):
            headers = {k.lower(): v for k, v in req.header_items()}
            captured["x-api-key"] = headers.get("x-api-key")
            return _Resp()

        with patch("axiom.wallet.wdk_wallet_client.urlopen", side_effect=_fake_urlopen):
            self.client._call_service("/balance", {"chain": "polygon"})  # noqa: SLF001
        self.assertEqual(captured["x-api-key"], "secret-key")


if __name__ == "__main__":
    unittest.main()
