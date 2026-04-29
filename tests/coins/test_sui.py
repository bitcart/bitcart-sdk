import bitcart
from bitcart import COINS, SUI
from bitcart.manager import APIManager

SUI_ADDRESS = "0x" + "1" * 64
SUI_RPC_URL = "http://localhost:5012"


def test_sui_is_registered():
    assert COINS["SUI"] is SUI
    assert bitcart.SUI is SUI
    assert "SUI" in bitcart.__all__


def test_sui_defaults():
    sui = SUI()

    assert sui.coin_name == "SUI"
    assert sui.friendly_name == "Sui"
    assert sui.rpc_url == SUI_RPC_URL
    assert sui.xpub_name == "Address"
    assert sui.EXPIRATION_KEY == "expiration"
    assert sui.is_eth_based is False


def test_manager_loads_sui_wallet():
    manager = APIManager({"SUI": [SUI_ADDRESS]})

    assert manager.wallets["SUI"][SUI_ADDRESS] == SUI(xpub=SUI_ADDRESS)
