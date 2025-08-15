# Makefile for test automation

.PHONY: help test test-unit test-integration test-e2e test-performance test-all coverage clean

help:
	@echo "Available commands:"
	@echo "  make test           - Run all tests"
	@echo "  make test-unit      - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make test-e2e       - Run end-to-end tests only"
	@echo "  make test-performance - Run performance tests only"
	@echo "  make test-watch     - Run tests in watch mode"
	@echo "  make coverage       - Generate coverage report"
	@echo "  make clean          - Clean test artifacts"

# Run all tests
test:
	pytest

# Run specific test categories
test-unit:
	pytest tests/unit -v -m unit

test-integration:
	pytest tests/integration -v -m integration

test-e2e:
	pytest tests/e2e -v -m e2e

test-performance:
	pytest tests/performance -v -m performance

# Run tests in watch mode
test-watch:
	pytest-watch

# Run all tests with detailed output
test-all:
	pytest -v --tb=long --maxfail=1

# Generate coverage report
coverage:
	pytest --cov=app --cov-report=html --cov-report=term
	@echo "Coverage report generated in htmlcov/index.html"

# Run tests in parallel
test-parallel:
	pytest -n auto

# Clean test artifacts
clean:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf test_uploads
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Install test dependencies
install-test:
	pip install pytest pytest-cov pytest-asyncio pytest-watch pytest-xdist factory-boy faker

# Run tests with different Python versions (requires tox)
test-tox:
	tox

# Lint tests
lint-tests:
	pylint tests/
	mypy tests/

# Format test code
format-tests:
	black tests/
	isort tests/