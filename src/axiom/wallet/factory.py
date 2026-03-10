from __future__ import annotations

from axiom.config import Settings
from axiom.wallet.mock_wallet_client import MockWalletClient
from axiom.wallet.wallet_client import WalletClient
from axiom.wallet.wdk_wallet_client import WdkWalletClient


def build_wallet_client(settings: Settings) -> WalletClient:
    if settings.wallet_mode == "wdk":
        return WdkWalletClient(module_name=settings.wdk_module)
    return MockWalletClient()
