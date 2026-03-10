from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Mandate:
    name: str
    description: str
    min_liquid_usdt: float
    pr_payout_usdt: float
    allowed_chains: list[str]
    evaluation_interval_seconds: int
    volatility_hedge_percent: float
    enable_hedge: bool = True


@dataclass(slots=True)
class PullRequestMergeEvent:
    merged_at: datetime
    author: str
    title: str
    url: str
    payout_address: str


@dataclass(slots=True)
class PoolQuote:
    chain: str
    protocol: str
    apy: float


@dataclass(slots=True)
class GasAndFeeSnapshot:
    chain: str
    estimated_tx_cost_usdt: float
    estimated_bridge_fee_usdt: float


@dataclass(slots=True)
class ProfitabilityDecision:
    is_profitable: bool
    expected_monthly_yield_usdt: float
    break_even_days: float
    reason: str
