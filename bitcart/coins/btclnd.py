"""BitcoinLND SDK coin class.

Provides the same interface as BTC but connects to the BTCLND daemon
(LND-backed) instead of Electrum.
"""

from .btc import BTC


class BTCLND(BTC):
    coin_name = "BTCLND"
    friendly_name = "Bitcoin (LND)"
    display_symbol = "BTC"  # Show "BTC" to customers on checkout, not "BTCLND"
    xpub_name = "Seed"
    RPC_URL = "http://localhost:5012"
    RPC_USER = "electrum"
    RPC_PASS = "electrumz"  # noqa
    # LND only supports hot wallets (seed-based), not watch-only
    hot_wallet_only = True
    # Lightning is always enabled with LND
    lightning_default = True
    # LND supports Tor hybrid mode
    supports_tor = True
    supports_zero_conf = True
    # Rate rules: define fixed SATS conversion (1 BTC = 100,000,000 SATS)
    # Uses BTCLND prefix (internal currency name) matching how the rate engine looks up rules
    rate_rules = "BTCLND_SATS = 100000000\nBTCLND_BTC = 1"

    async def open_channel(self, node_id: str, amount, private: bool = False) -> str:
        """Open lightning channel with announced/unannounced support."""
        return await self.server.open_channel(node_id, amount, private=private)
