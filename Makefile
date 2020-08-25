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
	pytest tests/

bitcoind:
	tests/regtest/start_bitcoind.sh

electrumx:
	tests/regtest/start_electrumx.sh

regtest:
	pytest tests/regtest.py --cov-append

ci: checkformat lint test
