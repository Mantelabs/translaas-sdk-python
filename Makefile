.PHONY: help test test-integration lint typecheck

help:
	@echo "Translaas Python SDK — development targets"
	@echo ""
	@echo "  make test              Run unit tests (excludes live API tests)"
	@echo "  make test-integration  Run live API integration tests (requires TRANSLAAS_API_KEY)"
	@echo "  make lint              Run ruff linter"
	@echo "  make typecheck         Run mypy"

test:
	pytest -m "not live"

test-integration:
	pytest -m live --no-cov -v

lint:
	python -m ruff check translaas/

typecheck:
	python -m mypy translaas/ --ignore-missing-imports --no-strict-optional
