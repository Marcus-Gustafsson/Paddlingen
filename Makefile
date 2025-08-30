# -------- Settings you can tweak --------
PATH_TO_MAIN_PY := .               # your source folder (e.g., ".", "my_app", or "src/my_app")

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
# Change $(PATH_TO_MAIN_PY) to your code path: ".", "my_app", or "src/my_app".
security-code:
	uv run -m bandit -q -r $(PATH_TO_MAIN_PY)

# -------- Security: dependencies (pip-audit) --------
# Checks installed packages for known vulnerabilities (requires network).
security-deps:
	uv run -m pip-audit

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
	@echo "make security-code  # Bandit scan of source code"
	@echo "make security-deps  # pip-audit dependency vulnerabilities"
	@echo "make security       # both security checks"
	@echo "make all-basic      # install -> lint -> format-check -> type-check -> test"
	@echo "make all-advanced   # install -> lint -> format-check -> type-check -> test -> security"
