.PHONY: help test lint format type-check check coverage clean

help:
	@echo "dataclaw - Development Targets"
	@echo "==============================="
	@echo ""
	@echo "Testing:"
	@echo "  make test              Run all tests with pytest"
	@echo "  make coverage          Run tests with coverage report (HTML + terminal)"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint              Check code style with ruff"
	@echo "  make format            Format code with ruff"
	@echo "  make type-check        Type check with mypy"
	@echo "  make check             Run lint + type-check"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean             Remove cache files and build artifacts"

test:
	python -m pytest tests/ -v

lint:
	python -m ruff check dataclaw/ tests/

format:
	python -m ruff format dataclaw/ tests/

type-check:
	python -m mypy dataclaw/ --ignore-missing-imports

check: lint type-check

coverage:
	python -m pytest tests/ --cov=dataclaw --cov-report=html --cov-report=term

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf dist/ build/ *.egg-info
	@echo "Cleaned up cache files and build artifacts"
