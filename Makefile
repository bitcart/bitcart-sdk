all: ci

lint:
	ruff check
	mypy bitcart

checkformat:
	ruff format --check

format:
	ruff format

test:
	pytest tests/ ${TEST_ARGS}

bitcoind:
	tests/regtest/start_bitcoind.sh

fulcrum:
	tests/regtest/start_fulcrum.sh

regtest:
	pytest tests/regtest.py --cov-append ${TEST_ARGS}

ci: checkformat lint test
