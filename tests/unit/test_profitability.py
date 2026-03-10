from __future__ import annotations

import unittest

from tests.bootstrap import SRC  # noqa: F401
from axiom.economics.profitability import evaluate_profitability


class ProfitabilityTests(unittest.TestCase):
    def test_returns_not_profitable_when_no_yield(self) -> None:
        decision = evaluate_profitability(1000, 0, 1, 1)
        self.assertFalse(decision.is_profitable)
        self.assertEqual(decision.expected_monthly_yield_usdt, 0.0)

    def test_profitable_when_break_even_under_threshold(self) -> None:
        decision = evaluate_profitability(2000, 12, 1, 1)
        self.assertTrue(decision.is_profitable)
        self.assertLessEqual(decision.break_even_days, 180)

    def test_not_profitable_when_break_even_too_long(self) -> None:
        decision = evaluate_profitability(200, 1, 20, 20)
        self.assertFalse(decision.is_profitable)
        self.assertGreater(decision.break_even_days, 180)


if __name__ == "__main__":
    unittest.main()
