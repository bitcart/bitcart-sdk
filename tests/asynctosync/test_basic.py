def test_sync_works(btc):
    assert isinstance(btc.help(), list)
    assert isinstance(btc.help(), list)  # ensure there are no loop mismatch error


def test_sync_works_with_properties(btc_wallet):
    assert isinstance(btc_wallet.node_id, str)  # property: special case
