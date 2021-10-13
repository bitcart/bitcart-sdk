import subprocess


def run_shell(args=[], timeout=30):
    process = subprocess.Popen(["tests/regtest/regtest.sh"] + args, stdout=subprocess.PIPE, universal_newlines=True)
    process.wait(timeout=timeout)
    assert process.returncode == 0
    return process.stdout.read().strip()


def data_check(data, key, check_type, length=None):
    assert key in data
    assert isinstance(data[key], check_type)
    if length:
        assert len(data[key]) == length


def patch_session(mocker, patched_session):
    mocker.patch(
        "bitcart.providers.jsonrpcrequests.RPCProxy.session", new_callable=mocker.PropertyMock(return_value=patched_session)
    )
