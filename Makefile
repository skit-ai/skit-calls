SHELL := /bin/zsh
python_version = 3.9

.PHONY: all test

lint:
	@isort skit_calls
	@isort tests
	@black skit_calls
	@black tests

typecheck:
	@echo -e "Running type checker"
	@mypy -p skit_calls

test: ## Run the tests.conf
	@pytest --cov=skit_calls --cov-report html --cov-report term:skip-covered tests/

all: lint typecheck test
