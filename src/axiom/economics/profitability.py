from __future__ import annotations

from axiom.models import ProfitabilityDecision


def evaluate_profitability(
    principal_usdt: float,
    apy: float,
    tx_cost_usdt: float,
    bridge_fee_usdt: float,
) -> ProfitabilityDecision:
    annual_yield = principal_usdt * max(apy, 0) / 100.0
    monthly_yield = annual_yield / 12.0
    total_cost = max(tx_cost_usdt, 0) + max(bridge_fee_usdt, 0)

    if monthly_yield <= 0:
        return ProfitabilityDecision(
            is_profitable=False,
            expected_monthly_yield_usdt=0.0,
            break_even_days=float("inf"),
            reason="Expected monthly yield is zero or negative.",
        )

    break_even_months = total_cost / monthly_yield
    break_even_days = break_even_months * 30.0

    # Economic soundness threshold inspired by the solution recommendation.
    is_profitable = break_even_days <= 180
    reason = (
        f"Projected break-even is {break_even_days:.1f} days."
        if is_profitable
        else f"Rejected: break-even is too long ({break_even_days:.1f} days)."
    )

    return ProfitabilityDecision(
        is_profitable=is_profitable,
        expected_monthly_yield_usdt=monthly_yield,
        break_even_days=break_even_days,
        reason=reason,
    )
