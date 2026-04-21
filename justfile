set no-exit-message

test-args := env("TEST_ARGS", "")

[private]
default:
    @just --list --unsorted --justfile {{ justfile() }}

# auto-format code with ruff
[group("Code quality")]
format:
    ruff format .

# run linters with autofix
[group("Code quality")]
lint:
    ruff check --fix .

# lint and format, fixing all issues
[group("Code quality")]
fix: format lint

# verify formatting with ruff
[group("Code quality")]
format-check:
    ruff format --check .

# verify linting
[group("Code quality")]
lint-check:
    ruff check .

# run type checking
[group("Code quality")]
typecheck:
    mypy bitcart

# run dependency checks
[group("Code quality")]
deps-check:
    deptry .

# run all checks without fixing
[group("Code quality")]
check: format-check lint-check typecheck deps-check

# run tests
[group("Code quality")]
test *args:
    pytest {{ trim(test-args + " " + args) }}

# run functional tests
[group("Code quality")]
functional *args:
    pytest tests/regtest.py --cov-append {{ trim(test-args + " " + args) }}

# run ci checks
[group("Code quality")]
ci *args: check (test args)

# docs

# build documentation
[group("Documentation")]
docs:
    zensical build

# serve documentation
[group("Documentation")]
docs-serve:
    zensical serve

# develop documentation with live reload
[group("Documentation")]
docs-dev:
    zensical serve

# btc-setup tasks

# start bitcoind
[group("BTC setup")]
bitcoind:
    tests/regtest/start_bitcoind.sh

# start fulcrum
[group("BTC setup")]
fulcrum:
    tests/regtest/start_fulcrum.sh
