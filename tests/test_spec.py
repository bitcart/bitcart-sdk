def test_spec(btc):
    assert btc.spec == btc.server.spec
    assert isinstance(btc.spec, dict)
    assert btc.spec.keys() == {"exceptions", "electrum_map", "version"}
