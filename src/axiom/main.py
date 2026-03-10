from __future__ import annotations

import argparse
import json
from pathlib import Path

from axiom.agent.engine import AxiomEngine
from axiom.config import load_settings
from axiom.github.github_client import GithubClient
from axiom.market.market_client import MarketClient
from axiom.models import Mandate
from axiom.wallet.factory import build_wallet_client


def load_mandate(path: str, fallback_settings) -> Mandate:
    mandate_path = Path(path)
    if mandate_path.exists():
        payload = json.loads(mandate_path.read_text(encoding="utf-8"))
        return Mandate(
            name=payload["name"],
            description=payload["description"],
            min_liquid_usdt=float(payload["min_liquid_usdt"]),
            pr_payout_usdt=float(payload["pr_payout_usdt"]),
            allowed_chains=list(payload["allowed_chains"]),
            evaluation_interval_seconds=int(payload["evaluation_interval_seconds"]),
            volatility_hedge_percent=float(payload["volatility_hedge_percent"]),
            enable_hedge=bool(payload.get("enable_hedge", True)),
        )

    return Mandate(
        name="axiom-env-mandate",
        description="Mandate loaded from environment variables.",
        min_liquid_usdt=fallback_settings.min_liquid_usdt,
        pr_payout_usdt=fallback_settings.pr_payout_usdt,
        allowed_chains=fallback_settings.allowed_chains,
        evaluation_interval_seconds=fallback_settings.evaluation_interval_seconds,
        volatility_hedge_percent=fallback_settings.volatility_hedge_percent,
        enable_hedge=fallback_settings.enable_hedge,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Axiom AFC autonomous treasury agent")
    parser.add_argument(
        "--rules",
        default="rules/mandate.example.json",
        help="Path to mandate JSON file",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run one evaluation cycle and exit",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = load_settings()
    mandate = load_mandate(args.rules, settings)

    wallet = build_wallet_client(settings)
    github = GithubClient(
        owner=settings.github_repo_owner,
        repo=settings.github_repo_name,
        token=settings.github_token,
        contributor_wallets_path=settings.contributor_wallets_path,
    )
    market = MarketClient(
        apy_api_url=settings.apy_api_url,
        gas_api_url=settings.gas_api_url,
        bridge_fee_usdt=settings.bridge_fee_usdt,
    )

    engine = AxiomEngine(
        mandate=mandate,
        wallet=wallet,
        github=github,
        market=market,
        checking_wallet_address=settings.checking_wallet_address,
        treasury_wallet_address=settings.treasury_wallet_address,
        usdt_token=settings.default_usdt_token,
        enable_yield_moves=settings.enable_yield_moves,
    )
    engine.run(once=args.once)


if __name__ == "__main__":
    main()
