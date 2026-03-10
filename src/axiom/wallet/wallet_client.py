from __future__ import annotations

from typing import Protocol


class WalletClient(Protocol):
    def get_balance(self, address: str, token: str) -> float:
        ...

    def transfer(self, token: str, from_address: str, to_address: str, amount: float, chain: str) -> str:
        ...

    def move_to_yield(self, token: str, from_address: str, amount: float, chain: str, protocol: str) -> str:
        ...

    def hedge_to_xaut(self, from_address: str, amount_usdt: float, chain: str) -> str:
        ...
