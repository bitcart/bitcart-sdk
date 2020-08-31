def test_sync_works(btc):
    assert isinstance(btc.help(), list)


def test_sync_works_with_properties(btc_wallet):
    assert isinstance(btc_wallet.node_id, str)  # property: special case
