.PHONY: ci lint test

ci: lint test

lint:
	uvx ruff check src
	uvx ruff format --check src

test:
	uvx pytest -q