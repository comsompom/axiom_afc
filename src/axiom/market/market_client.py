from __future__ import annotations

import json
from urllib.request import Request, urlopen

from axiom.models import GasAndFeeSnapshot, PoolQuote


class MarketClient:
    def __init__(self, apy_api_url: str, gas_api_url: str, bridge_fee_usdt: float) -> None:
        self.apy_api_url = apy_api_url
        self.gas_api_url = gas_api_url
        self.bridge_fee_usdt = bridge_fee_usdt

    def top_pool_for_chain(self, chain: str) -> PoolQuote:
        chain = chain.lower()
        if not self.apy_api_url:
            return self._mock_pool(chain)

        req = Request(self.apy_api_url, headers={"User-Agent": "axiom-afc-agent"})
        try:
            with urlopen(req, timeout=12) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except Exception:
            return self._mock_pool(chain)

        best = None
        for pool in payload.get("data", []):
            if str(pool.get("chain", "")).lower() != chain:
                continue
            if "apy" not in pool:
                continue
            apy = float(pool.get("apy", 0.0))
            # Filter obvious outliers/noise so profitability math is credible.
            if apy <= 0 or apy > 100:
                continue
            candidate = PoolQuote(
                chain=chain,
                protocol=str(pool.get("project", "unknown")),
                apy=apy,
            )
            if best is None or candidate.apy > best.apy:
                best = candidate
        return best if best is not None else self._mock_pool(chain)

    def gas_and_fees(self, chain: str) -> GasAndFeeSnapshot:
        if not self.gas_api_url:
            return self._mock_gas(chain)

        req = Request(self.gas_api_url, headers={"User-Agent": "axiom-afc-agent"})
        try:
            with urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            tx_cost = float(data.get("estimated_tx_cost_usdt", 0.5))
        except Exception:
            tx_cost = 0.5
        return GasAndFeeSnapshot(
            chain=chain,
            estimated_tx_cost_usdt=tx_cost,
            estimated_bridge_fee_usdt=self.bridge_fee_usdt,
        )

    def volatility_score(self) -> float:
        # In production this should come from an MCP-connected market signal.
        return 0.42

    def _mock_pool(self, chain: str) -> PoolQuote:
        default_apy = {"arbitrum": 8.2, "base": 7.5}.get(chain, 6.0)
        return PoolQuote(chain=chain, protocol="mock-aave", apy=default_apy)

    def _mock_gas(self, chain: str) -> GasAndFeeSnapshot:
        base_cost = {"arbitrum": 0.7, "base": 0.4}.get(chain, 0.6)
        return GasAndFeeSnapshot(
            chain=chain,
            estimated_tx_cost_usdt=base_cost,
            estimated_bridge_fee_usdt=self.bridge_fee_usdt,
        )
