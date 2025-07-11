import subprocess
from typing import Any


def run_shell(args=None, timeout=30):
    if args is None:
        args = []
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


def assert_contains(expected: dict[str, Any], actual: dict[str, Any]) -> None:
    missing = set(expected) - set(actual)
    if missing:
        raise AssertionError(f"Missing keys: {sorted(missing)}")
    mismatched = {k: (expected[k], actual[k]) for k in expected if actual[k] != expected[k]}
    if mismatched:
        msgs = [f"{k!r}: expected {exp!r}, got {got!r}" for k, (exp, got) in mismatched.items()]
        raise AssertionError("Mismatches:\n  " + "\n  ".join(msgs))
