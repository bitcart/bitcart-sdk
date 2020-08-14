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

ci: checkformat lint test
