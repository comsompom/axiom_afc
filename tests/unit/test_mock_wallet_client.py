from __future__ import annotations

import unittest

from tests.bootstrap import SRC  # noqa: F401
from axiom.wallet.mock_wallet_client import MockWalletClient


class MockWalletClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.wallet = MockWalletClient()

    def test_transfer_updates_balances(self) -> None:
        from_addr = "0xCheckingWallet"
        to_addr = "0xRecipient"
        start_from = self.wallet.get_balance(from_addr, "USDT")
        start_to = self.wallet.get_balance(to_addr, "USDT")

        tx_hash = self.wallet.transfer("USDT", from_addr, to_addr, 100, "polygon")
        self.assertIn("mock-tx-polygon-", tx_hash)
        self.assertEqual(self.wallet.get_balance(from_addr, "USDT"), start_from - 100)
        self.assertEqual(self.wallet.get_balance(to_addr, "USDT"), start_to + 100)

    def test_move_to_yield_moves_balance(self) -> None:
        from_addr = "0xCheckingWallet"
        tx_hash = self.wallet.move_to_yield("USDT", from_addr, 200, "bnb", "venus")
        self.assertIn("mock-deposit-bnb-", tx_hash)
        self.assertEqual(self.wallet.get_balance(from_addr, "USDT"), 1800.0)

    def test_transfer_raises_when_insufficient_balance(self) -> None:
        with self.assertRaises(RuntimeError):
            self.wallet.transfer("USDT", "0xCheckingWallet", "0xRecipient", 999999, "polygon")


if __name__ == "__main__":
    unittest.main()
