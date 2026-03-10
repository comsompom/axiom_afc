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
    contributor_wallets_path: str
    token_map_path: str
    protocol_map_path: str
    default_chain: str
    wdk_service_url: str
    wdk_service_timeout_seconds: int
    wdk_service_api_key: str
    enable_yield_moves: bool
    activity_log_path: str


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
        contributor_wallets_path=os.getenv("CONTRIBUTOR_WALLETS_PATH", "data/contributor_wallets.json").strip(),
        token_map_path=os.getenv("TOKEN_MAP_PATH", "config/token_map.json").strip(),
        protocol_map_path=os.getenv("PROTOCOL_MAP_PATH", "config/protocol_map.json").strip(),
        default_chain=os.getenv("DEFAULT_CHAIN", "arbitrum").strip().lower(),
        wdk_service_url=os.getenv("WDK_SERVICE_URL", "http://127.0.0.1:8787").strip(),
        wdk_service_timeout_seconds=int(os.getenv("WDK_SERVICE_TIMEOUT_SECONDS", "20")),
        wdk_service_api_key=os.getenv("WDK_SERVICE_API_KEY", "").strip(),
        enable_yield_moves=_bool_env("ENABLE_YIELD_MOVES", False),
        activity_log_path=os.getenv("ACTIVITY_LOG_PATH", "data/activity_log.jsonl").strip(),
    )
