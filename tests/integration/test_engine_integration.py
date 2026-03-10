from __future__ import annotations

import unittest
from datetime import datetime, timezone

from tests.bootstrap import SRC  # noqa: F401
from axiom.agent.engine import AxiomEngine
from axiom.models import GasAndFeeSnapshot, Mandate, PoolQuote, PullRequestMergeEvent


class StubWallet:
    def __init__(self, balance: float) -> None:
        self.balance = balance
        self.transfers: list[dict] = []
        self.yield_moves: list[dict] = []

    def get_balance(self, address: str, token: str) -> float:
        return self.balance

    def transfer(self, token: str, from_address: str, to_address: str, amount: float, chain: str) -> str:
        self.transfers.append(
            {"token": token, "from": from_address, "to": to_address, "amount": amount, "chain": chain}
        )
        self.balance -= amount
        return "0xtransfer"

    def move_to_yield(self, token: str, from_address: str, amount: float, chain: str, protocol: str) -> str:
        self.yield_moves.append(
            {"token": token, "from": from_address, "amount": amount, "chain": chain, "protocol": protocol}
        )
        self.balance -= amount
        return "0xyield"

    def hedge_to_xaut(self, from_address: str, amount_usdt: float, chain: str) -> str:
        return "0xhedge"


class StubGithub:
    def __init__(self, with_event: bool = True) -> None:
        self.with_event = with_event

    def recent_merged_prs(self, limit: int = 25) -> list[PullRequestMergeEvent]:
        if not self.with_event:
            return []
        return [
            PullRequestMergeEvent(
                merged_at=datetime.now(timezone.utc),
                author="alice",
                title="feat",
                url="https://example/pr/1",
                payout_address="0xabc",
            )
        ]


class StubMarket:
    def top_pool_for_chain(self, chain: str) -> PoolQuote:
        return PoolQuote(chain=chain, protocol="aave-v3", apy=12.0)

    def gas_and_fees(self, chain: str) -> GasAndFeeSnapshot:
        return GasAndFeeSnapshot(chain=chain, estimated_tx_cost_usdt=0.1, estimated_bridge_fee_usdt=0.2)

    def volatility_score(self) -> float:
        return 0.1


class EngineIntegrationTests(unittest.TestCase):
    def _mandate(self) -> Mandate:
        return Mandate(
            name="m",
            description="d",
            min_liquid_usdt=500,
            pr_payout_usdt=50,
            allowed_chains=["polygon", "bnb"],
            evaluation_interval_seconds=60,
            volatility_hedge_percent=0,
            enable_hedge=False,
        )

    def test_run_once_executes_payout_and_yield_when_enabled(self) -> None:
        wallet = StubWallet(balance=2000)
        engine = AxiomEngine(
            mandate=self._mandate(),
            wallet=wallet,
            github=StubGithub(with_event=True),
            market=StubMarket(),
            checking_wallet_address="0xcheck",
            treasury_wallet_address="0xtreasury",
            usdt_token="USDT",
            enable_yield_moves=True,
        )
        engine.run_once()
        self.assertEqual(len(wallet.transfers), 1)
        self.assertEqual(len(wallet.yield_moves), 1)

    def test_run_once_skips_yield_when_disabled(self) -> None:
        wallet = StubWallet(balance=2000)
        engine = AxiomEngine(
            mandate=self._mandate(),
            wallet=wallet,
            github=StubGithub(with_event=True),
            market=StubMarket(),
            checking_wallet_address="0xcheck",
            treasury_wallet_address="0xtreasury",
            usdt_token="USDT",
            enable_yield_moves=False,
        )
        engine.run_once()
        self.assertEqual(len(wallet.transfers), 1)
        self.assertEqual(len(wallet.yield_moves), 0)


if __name__ == "__main__":
    unittest.main()
