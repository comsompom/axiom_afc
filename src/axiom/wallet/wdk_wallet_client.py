from __future__ import annotations

import importlib
import json
from decimal import Decimal, ROUND_DOWN
from pathlib import Path
from typing import Any

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
    ) -> None:
        self.module_name = module_name
        self.sdk = self._load_sdk(module_name)
        self.allowed_chains = {c.lower() for c in allowed_chains}
        self.default_chain = default_chain.lower()
        self.token_map = self._load_json(token_map_path, "token map")
        self.protocol_map = self._load_json(protocol_map_path, "protocol map")
        if self.default_chain not in self.allowed_chains:
            raise RuntimeError(f"DEFAULT_CHAIN '{self.default_chain}' is not in ALLOWED_CHAINS.")

    def _load_sdk(self, module_name: str):
        try:
            return importlib.import_module(module_name)
        except ImportError as exc:
            raise RuntimeError(
                f"Could not import WDK module '{module_name}'. "
                "Install the official WDK SDK and set WDK_MODULE accordingly."
            ) from exc

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

    def _call_sdk(self, method_names: list[str], **kwargs: Any) -> Any:
        errors: list[str] = []
        for name in method_names:
            if not hasattr(self.sdk, name):
                continue
            fn = getattr(self.sdk, name)
            try:
                return fn(**kwargs)
            except TypeError as exc:
                errors.append(f"{name}: {exc}")
                continue
        if errors:
            raise RuntimeError(f"WDK method signature mismatch ({'; '.join(errors)})")
        raise RuntimeError(f"No supported WDK method found from: {', '.join(method_names)}")

    def get_balance(self, address: str, token: str) -> float:
        chain = self._resolve_chain(None)
        token_meta = self._token_meta(chain, token)
        try:
            raw = self._call_sdk(
                ["get_balance", "balance_of", "token_balance"],
                address=address,
                token_address=token_meta["address"],
                chain=chain,
            )
        except Exception as exc:
            raise RuntimeError(f"WDK get_balance failed for token={token}, chain={chain}.") from exc
        if isinstance(raw, (int, str)):
            return self._from_base_units(raw, int(token_meta["decimals"]))
        if isinstance(raw, float):
            return raw
        if isinstance(raw, dict):
            amount = raw.get("amount") or raw.get("balance")
            if amount is None:
                raise RuntimeError("WDK get_balance response missing amount.")
            return self._from_base_units(amount, int(token_meta["decimals"]))
        raise RuntimeError("Unsupported WDK get_balance response type.")

    def transfer(self, token: str, from_address: str, to_address: str, amount: float, chain: str) -> str:
        resolved_chain = self._resolve_chain(chain)
        token_meta = self._token_meta(resolved_chain, token)
        if not to_address:
            raise RuntimeError("Destination address is required for transfer.")
        amount_base_units = self._to_base_units(amount, int(token_meta["decimals"]))
        try:
            raw = self._call_sdk(
                ["transfer", "send_token", "erc20_transfer"],
                from_address=from_address,
                to_address=to_address,
                token_address=token_meta["address"],
                amount=amount_base_units,
                chain=resolved_chain,
            )
        except Exception as exc:
            raise RuntimeError(
                f"WDK transfer failed token={token} chain={resolved_chain} amount={amount}."
            ) from exc
        return self._extract_tx_hash(raw)

    def move_to_yield(self, token: str, from_address: str, amount: float, chain: str, protocol: str) -> str:
        resolved_chain = self._resolve_chain(chain)
        token_meta = self._token_meta(resolved_chain, token)
        amount_base_units = self._to_base_units(amount, int(token_meta["decimals"]))
        route = self.protocol_map.get("lending", {}).get(resolved_chain, {}).get(protocol, {})
        try:
            raw = self._call_sdk(
                ["deposit_to_protocol", "deposit", "lend"],
                from_address=from_address,
                token_address=token_meta["address"],
                amount=amount_base_units,
                chain=resolved_chain,
                protocol=protocol,
                route=route,
            )
        except Exception as exc:
            raise RuntimeError(
                f"WDK move_to_yield failed token={token} chain={resolved_chain} protocol={protocol}."
            ) from exc
        return self._extract_tx_hash(raw)

    def hedge_to_xaut(self, from_address: str, amount_usdt: float, chain: str) -> str:
        resolved_chain = self._resolve_chain(chain)
        usdt_meta = self._token_meta(resolved_chain, "USDt")
        xaut_meta = self._token_meta(resolved_chain, "XAUt")
        amount_base_units = self._to_base_units(amount_usdt, int(usdt_meta["decimals"]))
        route = self.protocol_map.get("swap", {}).get(resolved_chain, {}).get("USDt_to_XAUt", {})
        try:
            raw = self._call_sdk(
                ["swap", "swap_tokens"],
                from_address=from_address,
                chain=resolved_chain,
                from_token_address=usdt_meta["address"],
                to_token_address=xaut_meta["address"],
                amount=amount_base_units,
                route=route,
            )
        except Exception as exc:
            raise RuntimeError(
                f"WDK hedge_to_xaut failed chain={resolved_chain} amount={amount_usdt}."
            ) from exc
        return self._extract_tx_hash(raw)
