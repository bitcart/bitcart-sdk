set no-exit-message

test-args := env("TEST_ARGS", "")

[private]
default:
    @just --list --unsorted --justfile {{ justfile() }}

## CODE QUALITY

# Auto-format code
[group("Code quality")]
format *files:
    ruff format {{ files }}

# Run linters with autofix
[group("Code quality")]
lint:
    ruff check --fix .

# Format and lint, fixing all issues
[group("Code quality")]
fix: format lint

# Verify formatting
[group("Code quality")]
format-check *files:
    ruff format --check {{ files }}

# Verify linting
[group("Code quality")]
lint-check:
    ruff check .

# Run type checking
[group("Code quality")]
typecheck:
    mypy bitcart

# Run dependency checks
[group("Code quality")]
deps-check:
    deptry .

# Run all checks without fixing
[group("Code quality")]
check: format-check lint-check typecheck deps-check

# Run tests
[group("Code quality")]
test *args:
    pytest {{ trim(test-args + " " + args) }}

# Run CI checks
[group("Code quality")]
ci *args: check (test args)

## TESTING

# Run functional tests
[group("Testing")]
test-functional *args:
    pytest tests/regtest.py --cov-append {{ trim(test-args + " " + args) }}

## DOCUMENTATION

# Build documentation
[group("Documentation")]
docs-build:
    zensical build

# Serve documentation
[group("Documentation")]
docs-serve:
    zensical serve

# Develop documentation with live reload
[group("Documentation")]
docs-dev:
    zensical serve

## REGTEST SETUP

# Start bitcoind
[group("Regtest setup")]
bitcoind:
    tests/regtest/start_bitcoind.sh

# Start fulcrum
[group("Regtest setup")]
fulcrum:
    tests/regtest/start_fulcrum.sh
