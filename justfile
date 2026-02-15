set no-exit-message := true

test-args := env("TEST_ARGS", "")

[private]
default:
    @just --list --unsorted --justfile {{ justfile() }}

# run linters with autofix
[group("Linting")]
lint:
    ruff format . && ruff check --fix .

# run linters (check only)
[group("Linting")]
lint-check:
    ruff format --check . && ruff check .

# run type checking
[group("Linting")]
lint-types:
    mypy bitcart

# run tests
[group("Testing")]
test *args:
    pytest {{ trim(test-args + " " + args) }}

# run functional tests
[group("Testing")]
functional *args:
    pytest tests/regtest.py --cov-append {{ trim(test-args + " " + args) }}

# run ci checks (without tests)
[group("CI")]
ci-lint: lint-check lint-types

# run ci checks
[group("CI")]
ci *args: ci-lint (test args)

# docs

# build documentation
[group("Documentation")]
docs:
    mkdocs build

# serve documentation
[group("Documentation")]
docs-serve:
    mkdocs serve

# develop documentation with live reload
[group("Documentation")]
docs-dev:
    mkdocs serve --livereload

# btc-setup tasks

# start bitcoind
[group("BTC setup")]
bitcoind:
    tests/regtest/start_bitcoind.sh

# start fulcrum
[group("BTC setup")]
fulcrum:
    tests/regtest/start_fulcrum.sh
