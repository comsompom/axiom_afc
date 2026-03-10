from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(slots=True)
class Settings:
    wallet_mode: str
    wdk_module: str
    treasury_wallet_address: str
    checking_wallet_address: str
    default_usdt_token: str
    min_liquid_usdt: float
    pr_payout_usdt: float
    volatility_hedge_percent: float
    evaluation_interval_seconds: int
    enable_hedge: bool
    allowed_chains: list[str]
    bridge_fee_usdt: float
    github_repo_owner: str
    github_repo_name: str
    github_token: str
    apy_api_url: str
    gas_api_url: str


def load_settings() -> Settings:
    load_dotenv()
    allowed = [c.strip().lower() for c in os.getenv("ALLOWED_CHAINS", "arbitrum,base").split(",") if c.strip()]
    return Settings(
        wallet_mode=os.getenv("WALLET_MODE", "mock").strip().lower(),
        wdk_module=os.getenv("WDK_MODULE", "wdk").strip(),
        treasury_wallet_address=os.getenv("TREASURY_WALLET_ADDRESS", "0xTreasuryWallet"),
        checking_wallet_address=os.getenv("CHECKING_WALLET_ADDRESS", "0xCheckingWallet"),
        default_usdt_token=os.getenv("DEFAULT_USDT_TOKEN", "USDt"),
        min_liquid_usdt=float(os.getenv("MIN_LIQUID_USDT", "500")),
        pr_payout_usdt=float(os.getenv("PR_PAYOUT_USDT", "50")),
        volatility_hedge_percent=float(os.getenv("VOLATILITY_HEDGE_PERCENT", "0.1")),
        evaluation_interval_seconds=int(os.getenv("EVALUATION_INTERVAL_SECONDS", "600")),
        enable_hedge=_bool_env("ENABLE_HEDGE", True),
        allowed_chains=allowed or ["arbitrum", "base"],
        bridge_fee_usdt=float(os.getenv("BRIDGE_FEE_USDT", "3")),
        github_repo_owner=os.getenv("GITHUB_REPO_OWNER", ""),
        github_repo_name=os.getenv("GITHUB_REPO_NAME", ""),
        github_token=os.getenv("GITHUB_TOKEN", ""),
        apy_api_url=os.getenv("APY_API_URL", "https://yields.llama.fi/pools"),
        gas_api_url=os.getenv("GAS_API_URL", "").strip(),
    )
