from __future__ import annotations

import time

from axiom.economics.profitability import evaluate_profitability
from axiom.github.github_client import GithubClient
from axiom.market.market_client import MarketClient
from axiom.models import Mandate
from axiom.utils.logger import log, log_action
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
        enable_yield_moves: bool = True,
        activity_log_path: str = "data/activity_log.jsonl",
    ) -> None:
        self.mandate = mandate
        self.wallet = wallet
        self.github = github
        self.market = market
        self.checking_wallet_address = checking_wallet_address
        self.treasury_wallet_address = treasury_wallet_address
        self.usdt_token = usdt_token
        self.enable_yield_moves = enable_yield_moves
        self.activity_log_path = activity_log_path

    def run(self, once: bool = False) -> None:
        log(f"Starting Axiom loop for mandate: {self.mandate.name}")
        while True:
            self.run_once()
            if once:
                return
            time.sleep(self.mandate.evaluation_interval_seconds)

    def run_once(self) -> None:
        log_action("cycle_start", "ok", {"mandate": self.mandate.name}, self.activity_log_path)
        self._process_pr_rewards()
        self._optimize_treasury()
        self._optional_hedge()

    def _process_pr_rewards(self) -> None:
        events = self.github.recent_merged_prs()
        if not events:
            log("No new merged PR events.")
            return

        for event in events:
            try:
                balance = self.wallet.get_balance(self.checking_wallet_address, self.usdt_token)
            except Exception as exc:
                log(f"Skip payout checks due to wallet balance error: {exc}")
                log_action("payout_balance_check", "error", {"error": str(exc)}, self.activity_log_path)
                return
            if balance < self.mandate.pr_payout_usdt:
                log(
                    f"Skip payout for {event.author}: "
                    f"insufficient balance ({balance:.2f} {self.usdt_token})."
                )
                log_action(
                    "payout_skip",
                    "skipped",
                    {"author": event.author, "reason": "insufficient_balance", "balance": balance},
                    self.activity_log_path,
                )
                continue
            try:
                tx_hash = self.wallet.transfer(
                    token=self.usdt_token,
                    from_address=self.checking_wallet_address,
                    to_address=event.payout_address,
                    amount=self.mandate.pr_payout_usdt,
                    chain=self.mandate.allowed_chains[0],
                )
            except Exception as exc:
                log(f"Payout failed for {event.author}: {exc}")
                log_action(
                    "payout_transfer",
                    "error",
                    {"author": event.author, "error": str(exc)},
                    self.activity_log_path,
                )
                continue
            log(
                f"Paid {self.mandate.pr_payout_usdt:.2f} {self.usdt_token} to {event.author} "
                f"for merged PR '{event.title}'. tx={tx_hash}"
            )
            log_action(
                "payout_transfer",
                "ok",
                {"author": event.author, "amount": self.mandate.pr_payout_usdt, "tx_hash": tx_hash},
                self.activity_log_path,
            )

    def _optimize_treasury(self) -> None:
        if not self.enable_yield_moves:
            log("Yield deployment disabled by ENABLE_YIELD_MOVES setting.")
            log_action("yield_move", "skipped", {"reason": "disabled"}, self.activity_log_path)
            return
        try:
            balance = self.wallet.get_balance(self.checking_wallet_address, self.usdt_token)
        except Exception as exc:
            log(f"Skip treasury optimization due to wallet balance error: {exc}")
            log_action("yield_balance_check", "error", {"error": str(exc)}, self.activity_log_path)
            return
        excess = balance - self.mandate.min_liquid_usdt
        if excess <= 0:
            log(
                f"Liquidity reserve respected ({balance:.2f} {self.usdt_token} <= "
                f"target {self.mandate.min_liquid_usdt:.2f})."
            )
            log_action(
                "yield_move",
                "skipped",
                {"reason": "no_excess_balance", "balance": balance},
                self.activity_log_path,
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
            log_action(
                "yield_move",
                "skipped",
                {"reason": "not_profitable", "break_even_days": decision.break_even_days},
                self.activity_log_path,
            )
            return

        try:
            tx_hash = self.wallet.move_to_yield(
                token=self.usdt_token,
                from_address=self.checking_wallet_address,
                amount=excess,
                chain=best_quote.chain,
                protocol=best_quote.protocol,
            )
        except Exception as exc:
            log(f"Treasury move failed/skipped: {exc}")
            log_action("yield_move", "error", {"error": str(exc)}, self.activity_log_path)
            return
        log(
            f"Moved {excess:.2f} {self.usdt_token} to {best_quote.protocol} on {best_quote.chain}. "
            f"tx={tx_hash}"
        )
        log_action(
            "yield_move",
            "ok",
            {
                "amount": excess,
                "chain": best_quote.chain,
                "protocol": best_quote.protocol,
                "tx_hash": tx_hash,
            },
            self.activity_log_path,
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
