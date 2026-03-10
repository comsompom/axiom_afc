from __future__ import annotations

from axiom.config import Settings
from axiom.wallet.mock_wallet_client import MockWalletClient
from axiom.wallet.wallet_client import WalletClient
from axiom.wallet.wdk_wallet_client import WdkWalletClient


def build_wallet_client(settings: Settings) -> WalletClient:
    if settings.wallet_mode == "wdk":
        return WdkWalletClient(
            module_name=settings.wdk_module,
            token_map_path=settings.token_map_path,
            protocol_map_path=settings.protocol_map_path,
            allowed_chains=settings.allowed_chains,
            default_chain=settings.default_chain,
            wdk_service_url=settings.wdk_service_url,
            timeout_seconds=settings.wdk_service_timeout_seconds,
            api_key=settings.wdk_service_api_key,
        )
    return MockWalletClient()
