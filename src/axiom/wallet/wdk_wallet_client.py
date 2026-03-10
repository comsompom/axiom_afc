from __future__ import annotations

import json
from decimal import Decimal, ROUND_DOWN
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from axiom.wallet.wallet_client import WalletClient


class WdkWalletClient(WalletClient):
    """
    Adapter to isolate WDK-specific logic.
    This class is intentionally explicit so hackathon judges can see where
    self-custodial wallet operations are bound to WDK.
    """

    def __init__(
        self,
        module_name: str,
        token_map_path: str,
        protocol_map_path: str,
        allowed_chains: list[str],
        default_chain: str,
        wdk_service_url: str,
        timeout_seconds: int,
        api_key: str = "",
    ) -> None:
        self.module_name = module_name
        self.wdk_service_url = wdk_service_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.api_key = api_key
        self.allowed_chains = {c.lower() for c in allowed_chains}
        self.default_chain = default_chain.lower()
        self.token_map = self._load_json(token_map_path, "token map")
        self.protocol_map = self._load_json(protocol_map_path, "protocol map")
        if self.default_chain not in self.allowed_chains:
            raise RuntimeError(f"DEFAULT_CHAIN '{self.default_chain}' is not in ALLOWED_CHAINS.")

    def _load_json(self, path: str, label: str) -> dict[str, Any]:
        target = Path(path)
        if not target.exists():
            raise RuntimeError(f"Missing {label} file at '{path}'.")
        try:
            return json.loads(target.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid JSON in {label} file '{path}'.") from exc

    def _resolve_chain(self, chain: str | None) -> str:
        resolved = (chain or self.default_chain).lower()
        if resolved not in self.allowed_chains:
            raise RuntimeError(f"Chain '{resolved}' is not allowed.")
        return resolved

    def _token_meta(self, chain: str, token: str) -> dict[str, Any]:
        try:
            chain_tokens = self.token_map[chain]
            token_meta = chain_tokens[token]
            if "address" not in token_meta or "decimals" not in token_meta:
                raise KeyError
            return token_meta
        except KeyError as exc:
            raise RuntimeError(f"Token '{token}' not configured for chain '{chain}' in token map.") from exc

    def _to_base_units(self, amount: float, decimals: int) -> int:
        if amount <= 0:
            raise RuntimeError("Amount must be positive.")
        q = Decimal("1").scaleb(-decimals)
        units = (Decimal(str(amount)).quantize(q, rounding=ROUND_DOWN) * (Decimal(10) ** decimals)).to_integral_value()
        return int(units)

    def _from_base_units(self, amount: int | str, decimals: int) -> float:
        return float(Decimal(str(amount)) / (Decimal(10) ** decimals))

    def _extract_tx_hash(self, raw: Any) -> str:
        if isinstance(raw, str):
            return raw
        if isinstance(raw, dict):
            for key in ("tx_hash", "transactionHash", "hash"):
                value = raw.get(key)
                if value:
                    return str(value)
        for key in ("tx_hash", "transactionHash", "hash"):
            if hasattr(raw, key):
                value = getattr(raw, key)
                if value:
                    return str(value)
        raise RuntimeError("WDK response does not include a tx hash.")

    def _call_service(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        req = Request(
            f"{self.wdk_service_url}{endpoint}",
            data=body,
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(req, timeout=self.timeout_seconds) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            raise RuntimeError(f"WDK service request failed: {endpoint}") from exc
        if not isinstance(data, dict):
            raise RuntimeError(f"WDK service returned invalid response for {endpoint}.")
        if not data.get("ok", False):
            raise RuntimeError(str(data.get("error", f"WDK service error at {endpoint}")))
        return data

    def get_balance(self, address: str, token: str) -> float:
        chain = self._resolve_chain(None)
        token_meta = self._token_meta(chain, token)
        data = self._call_service(
            "/balance",
            {
                "chain": chain,
                "address": address,
                "token_symbol": token,
                "token_address": token_meta["address"],
                "decimals": int(token_meta["decimals"]),
            },
        )
        amount = data.get("balance")
        if amount is None:
            raise RuntimeError("WDK service balance response missing balance.")
        return float(amount)

    def transfer(self, token: str, from_address: str, to_address: str, amount: float, chain: str) -> str:
        resolved_chain = self._resolve_chain(chain)
        token_meta = self._token_meta(resolved_chain, token)
        if not to_address:
            raise RuntimeError("Destination address is required for transfer.")
        amount_base_units = self._to_base_units(amount, int(token_meta["decimals"]))
        data = self._call_service(
            "/transfer",
            {
                "chain": resolved_chain,
                "token_symbol": token,
                "token_address": token_meta["address"],
                "from_address": from_address,
                "to_address": to_address,
                "amount": str(amount_base_units),
                "decimals": int(token_meta["decimals"]),
            },
        )
        return self._extract_tx_hash(data)

    def move_to_yield(self, token: str, from_address: str, amount: float, chain: str, protocol: str) -> str:
        resolved_chain = self._resolve_chain(chain)
        token_meta = self._token_meta(resolved_chain, token)
        amount_base_units = self._to_base_units(amount, int(token_meta["decimals"]))
        route = self.protocol_map.get("lending", {}).get(resolved_chain, {}).get(protocol, {})
        if not route:
            raise RuntimeError(
                f"No lending route configured for protocol={protocol} on chain={resolved_chain}."
            )
        data = self._call_service(
            "/deposit",
            {
                "chain": resolved_chain,
                "token_symbol": token,
                "token_address": token_meta["address"],
                "from_address": from_address,
                "amount": str(amount_base_units),
                "protocol": protocol,
                "route": route,
                "decimals": int(token_meta["decimals"]),
            },
        )
        return self._extract_tx_hash(data)

    def hedge_to_xaut(self, from_address: str, amount_usdt: float, chain: str) -> str:
        resolved_chain = self._resolve_chain(chain)
        usdt_meta = self._token_meta(resolved_chain, "USDT")
        swap_key = "USDT_to_BINOM"
        route = self.protocol_map.get("swap", {}).get(resolved_chain, {}).get(swap_key, {})
        if not route:
            raise RuntimeError(f"No swap route configured for {swap_key} on chain={resolved_chain}.")
        to_token_symbol = str(route.get("to_token_symbol", "BINOM"))
        to_token_meta = self._token_meta(resolved_chain, to_token_symbol)
        amount_base_units = self._to_base_units(amount_usdt, int(usdt_meta["decimals"]))
        data = self._call_service(
            "/swap",
            {
                "chain": resolved_chain,
                "from_address": from_address,
                "from_token_symbol": "USDT",
                "from_token_address": usdt_meta["address"],
                "to_token_symbol": to_token_symbol,
                "to_token_address": to_token_meta["address"],
                "amount": str(amount_base_units),
                "route": route,
            },
        )
        return self._extract_tx_hash(data)
