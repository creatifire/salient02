# Makefile for Python code quality tools

.PHONY: help install lint format typecheck fix all

# Default target
help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  install    Install development dependencies (excluding ruff/ty which are system-level)"
	@echo "  lint       Run ruff for linting and style checking"
	@echo "  format     Run ruff for formatting check"
	@echo "  typecheck  Run ty for static type analysis"
	@echo "  fix        Run ruff and apply automatic fixes"
	@echo "  all        Run lint, format check, and typecheck"

install:
	pip install -r requirements-dev.txt

lint:
	ruff check backend/

format:
	ruff format --check backend/

typecheck:
	ty check backend/

fix:
	ruff check --fix backend/
	ruff format backend/

all: lint format typecheck
