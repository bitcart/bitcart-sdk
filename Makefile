all: ci

lint:
	flake8
	mypy bitcart

checkformat:
	black --check .
	isort --check .

format:
	black .
	isort .

test:
	pytest tests/ ${TEST_ARGS}

bitcoind:
	tests/regtest/start_bitcoind.sh

fulcrum:
	tests/regtest/start_fulcrum.sh

regtest:
	pytest tests/regtest.py --cov-append ${TEST_ARGS}

ci: checkformat lint test
