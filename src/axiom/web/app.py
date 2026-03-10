from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, render_template

from axiom.config import Settings, load_settings
from axiom.github.github_client import GithubClient
from axiom.market.market_client import MarketClient
from axiom.wallet.factory import build_wallet_client
from axiom.wallet.wallet_client import WalletClient


def _safe_balance(wallet: WalletClient, address: str, token: str) -> tuple[float | None, str | None]:
    try:
        return wallet.get_balance(address, token), None
    except Exception as exc:
        return None, str(exc)


def collect_status(
    settings: Settings,
    wallet: WalletClient,
    github: GithubClient,
    market: MarketClient,
) -> dict:
    balance, balance_error = _safe_balance(wallet, settings.checking_wallet_address, settings.default_usdt_token)
    chain_quotes: list[dict] = []
    for chain in settings.allowed_chains:
        quote = market.top_pool_for_chain(chain)
        fees = market.gas_and_fees(chain)
        chain_quotes.append(
            {
                "chain": chain,
                "protocol": quote.protocol,
                "apy": round(quote.apy, 4),
                "tx_cost_usdt": round(fees.estimated_tx_cost_usdt, 4),
                "bridge_fee_usdt": round(fees.estimated_bridge_fee_usdt, 4),
            }
        )

    merged_events = github.recent_merged_prs(limit=10)
    event_preview = [
        {"author": e.author, "title": e.title, "url": e.url, "payout_address": e.payout_address}
        for e in merged_events[:5]
    ]
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "wallet_mode": settings.wallet_mode,
        "checking_wallet_address": settings.checking_wallet_address,
        "treasury_wallet_address": settings.treasury_wallet_address,
        "default_token": settings.default_usdt_token,
        "checking_balance": balance,
        "checking_balance_error": balance_error,
        "allowed_chains": settings.allowed_chains,
        "yield_moves_enabled": settings.enable_yield_moves,
        "hedge_enabled": settings.enable_hedge,
        "chain_quotes": chain_quotes,
        "merged_pr_count": len(merged_events),
        "merged_pr_preview": event_preview,
    }


def create_app() -> Flask:
    app = Flask(__name__, template_folder=str(Path(__file__).with_name("templates")))

    @app.get("/")
    def dashboard():
        settings = load_settings()
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
        status = collect_status(settings, wallet, github, market)
        return render_template("dashboard.html", status=status)

    @app.get("/api/status")
    def api_status():
        settings = load_settings()
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
        status = collect_status(settings, wallet, github, market)
        return jsonify(status)

    return app


def main() -> None:
    app = create_app()
    app.run(host="127.0.0.1", port=5050, debug=False)


if __name__ == "__main__":
    main()
