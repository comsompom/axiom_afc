from __future__ import annotations

import time

from axiom.economics.profitability import evaluate_profitability
from axiom.github.github_client import GithubClient
from axiom.market.market_client import MarketClient
from axiom.models import Mandate
from axiom.utils.logger import log
from axiom.wallet.wallet_client import WalletClient


class AxiomEngine:
    def __init__(
        self,
        mandate: Mandate,
        wallet: WalletClient,
        github: GithubClient,
        market: MarketClient,
        checking_wallet_address: str,
        treasury_wallet_address: str,
        usdt_token: str = "USDt",
    ) -> None:
        self.mandate = mandate
        self.wallet = wallet
        self.github = github
        self.market = market
        self.checking_wallet_address = checking_wallet_address
        self.treasury_wallet_address = treasury_wallet_address
        self.usdt_token = usdt_token

    def run(self, once: bool = False) -> None:
        log(f"Starting Axiom loop for mandate: {self.mandate.name}")
        while True:
            self.run_once()
            if once:
                return
            time.sleep(self.mandate.evaluation_interval_seconds)

    def run_once(self) -> None:
        self._process_pr_rewards()
        self._optimize_treasury()
        self._optional_hedge()

    def _process_pr_rewards(self) -> None:
        events = self.github.recent_merged_prs()
        if not events:
            log("No new merged PR events.")
            return

        for event in events:
            balance = self.wallet.get_balance(self.checking_wallet_address, self.usdt_token)
            if balance < self.mandate.pr_payout_usdt:
                log(
                    f"Skip payout for {event.author}: "
                    f"insufficient balance ({balance:.2f} {self.usdt_token})."
                )
                continue
            tx_hash = self.wallet.transfer(
                token=self.usdt_token,
                from_address=self.checking_wallet_address,
                to_address=event.payout_address,
                amount=self.mandate.pr_payout_usdt,
                chain=self.mandate.allowed_chains[0],
            )
            log(
                f"Paid {self.mandate.pr_payout_usdt:.2f} {self.usdt_token} to {event.author} "
                f"for merged PR '{event.title}'. tx={tx_hash}"
            )

    def _optimize_treasury(self) -> None:
        balance = self.wallet.get_balance(self.checking_wallet_address, self.usdt_token)
        excess = balance - self.mandate.min_liquid_usdt
        if excess <= 0:
            log(
                f"Liquidity reserve respected ({balance:.2f} {self.usdt_token} <= "
                f"target {self.mandate.min_liquid_usdt:.2f})."
            )
            return

        best_quote = None
        best_fee = None
        for chain in self.mandate.allowed_chains:
            quote = self.market.top_pool_for_chain(chain)
            fees = self.market.gas_and_fees(chain)
            if best_quote is None or quote.apy > best_quote.apy:
                best_quote = quote
                best_fee = fees

        if best_quote is None or best_fee is None:
            log("No eligible lending destination found.")
            return

        decision = evaluate_profitability(
            principal_usdt=excess,
            apy=best_quote.apy,
            tx_cost_usdt=best_fee.estimated_tx_cost_usdt,
            bridge_fee_usdt=best_fee.estimated_bridge_fee_usdt,
        )

        log(
            "Profitability check: "
            f"excess={excess:.2f} {self.usdt_token}, apy={best_quote.apy:.2f}%, "
            f"monthly_yield={decision.expected_monthly_yield_usdt:.2f}, "
            f"break_even_days={decision.break_even_days:.1f}"
        )

        if not decision.is_profitable:
            log(f"Treasury move skipped. {decision.reason}")
            return

        tx_hash = self.wallet.move_to_yield(
            token=self.usdt_token,
            from_address=self.checking_wallet_address,
            amount=excess,
            chain=best_quote.chain,
            protocol=best_quote.protocol,
        )
        log(
            f"Moved {excess:.2f} {self.usdt_token} to {best_quote.protocol} on {best_quote.chain}. "
            f"tx={tx_hash}"
        )

    def _optional_hedge(self) -> None:
        if not self.mandate.enable_hedge or self.mandate.volatility_hedge_percent <= 0:
            return

        score = self.market.volatility_score()
        if score < 0.8:
            log(f"Volatility score {score:.2f} below hedge threshold.")
            return

        balance = self.wallet.get_balance(self.checking_wallet_address, self.usdt_token)
        hedge_amount = max(0.0, balance * self.mandate.volatility_hedge_percent)
        if hedge_amount <= 0:
            return
        chain = self.mandate.allowed_chains[0]
        tx_hash = self.wallet.hedge_to_xaut(
            from_address=self.checking_wallet_address,
            amount_usdt=hedge_amount,
            chain=chain,
        )
        log(f"Hedged {hedge_amount:.2f} USDt to XAUt on {chain}. tx={tx_hash}")
