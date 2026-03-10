from __future__ import annotations

import uuid
from collections import defaultdict

from axiom.wallet.wallet_client import WalletClient


class MockWalletClient(WalletClient):
    def __init__(self) -> None:
        self._balances = defaultdict(float)
        self._balances["0xCheckingWallet:USDt"] = 2000.0
        self._balances["0xTreasuryWallet:USDt"] = 300.0
        self._balances["0xCheckingWallet:USDT"] = 2000.0
        self._balances["0xTreasuryWallet:USDT"] = 300.0
        self._balances["0x107119102c2EC84099cDce3D5eFDE2dcbf4DEB2a:USDT"] = 2000.0

    def _key(self, address: str, token: str) -> str:
        return f"{address}:{token}"

    def get_balance(self, address: str, token: str) -> float:
        return float(self._balances[self._key(address, token)])

    def transfer(self, token: str, from_address: str, to_address: str, amount: float, chain: str) -> str:
        if amount <= 0:
            raise RuntimeError("Transfer amount must be positive.")
        key_from = self._key(from_address, token)
        key_to = self._key(to_address, token)
        if self._balances[key_from] < amount:
            raise RuntimeError("Insufficient mock balance for transfer.")
        self._balances[key_from] -= amount
        self._balances[key_to] += amount
        return f"mock-tx-{chain}-{uuid.uuid4().hex[:10]}"

    def move_to_yield(self, token: str, from_address: str, amount: float, chain: str, protocol: str) -> str:
        if amount <= 0:
            raise RuntimeError("Yield move amount must be positive.")
        key_from = self._key(from_address, token)
        if self._balances[key_from] < amount:
            raise RuntimeError("Insufficient mock balance for yield move.")
        self._balances[key_from] -= amount
        self._balances[self._key(f"yield:{chain}:{protocol}", token)] += amount
        return f"mock-deposit-{chain}-{uuid.uuid4().hex[:10]}"

    def hedge_to_xaut(self, from_address: str, amount_usdt: float, chain: str) -> str:
        self._balances[self._key(from_address, "USDt")] -= amount_usdt
        self._balances[self._key(from_address, "XAUt")] += amount_usdt
        return f"mock-hedge-{chain}-{uuid.uuid4().hex[:10]}"
