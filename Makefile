# -------- Settings you can tweak --------
SECURITY_CODE_PATHS := app migrations config.py wsgi.py

# Use bash for recipes
SHELL := /usr/bin/env bash

# -------- PHONY targets --------
.PHONY: install test lint format format-check type-check security-code security-deps security all-basic all-advanced help

# -------- Install all deps into .venv --------
# Creates .venv (if missing) and installs runtime + dev tools via UV.
install:
	uv sync

# -------- Run tests --------
# Use uv run so you don't need to activate the venv.
test:
	uv run -m pytest -q

# -------- Lint (Ruff) --------
lint:
	uv run -m ruff check .

# -------- Format (Black) --------
format:
	uv run -m black .

# -------- Format check (no changes) --------
format-check:
	uv run -m black --check .

# ---------- Type checking ------------
type-check:
	uv run -m mypy .

# -------- Security: source code (Bandit) --------
# Scan only this project's Python code, not the whole repo root or .venv.
security-code:
	uv run python -m bandit -q -r $(SECURITY_CODE_PATHS)

# -------- Security: dependencies (pip-audit) --------
# Audit the project's locked dependencies, not unrelated tools in the whole venv.
security-deps:
	uv export --frozen --all-groups --format requirements.txt --no-hashes --no-header --no-annotate --no-emit-project > /tmp/paddling-pip-audit-requirements.txt
	uv run python -m pip_audit -r /tmp/paddling-pip-audit-requirements.txt

# -------- Aggregate security --------
security: security-code security-deps

# -------- Aggregates to simulate CI locally --------
# Basic: install -> lint -> format-check -> type-check -> test
all-basic: install lint format-check type-check test

# Advanced: basic + security
all-advanced: install lint format-check type-check test security

# -------- Helper: list commands --------
help:
	@echo "make install        # create .venv and install deps (UV)"
	@echo "make test           # run tests (pytest) via UV"
	@echo "make lint           # lint with ruff"
	@echo "make format         # format with black"
	@echo "make format-check   # verify formatting"
	@echo "make type-check     # type check source code"
	@echo "make security-code  # Bandit scan of project Python code"
	@echo "make security-deps  # pip-audit dependency vulnerabilities"
	@echo "make security       # both security checks"
	@echo "make all-basic      # install -> lint -> format-check -> type-check -> test"
	@echo "make all-advanced   # install -> lint -> format-check -> type-check -> test -> security"
