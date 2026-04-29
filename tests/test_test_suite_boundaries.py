import ast
from pathlib import Path

SYNC_DEPENDENT_TESTS = {"test_get_tx", "test_get_address"}


def get_test_names(test_file: Path) -> set[str]:
    tree = ast.parse(test_file.read_text())
    return {node.name for node in tree.body if isinstance(node, ast.AsyncFunctionDef | ast.FunctionDef)}


def test_default_btc_without_wallet_tests_do_not_include_sync_dependent_cases():
    test_names = get_test_names(Path("tests/coins/btc/test_without_wallet.py"))

    assert test_names.isdisjoint(SYNC_DEPENDENT_TESTS)


def test_regtest_suite_includes_sync_dependent_cases():
    test_names = get_test_names(Path("tests/regtest.py"))

    assert SYNC_DEPENDENT_TESTS.issubset(test_names)
