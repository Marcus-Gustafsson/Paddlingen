"""Tests for environment-driven application configuration."""

from __future__ import annotations

import importlib
import sys
from types import ModuleType

import pytest


def reload_config_module() -> ModuleType:
    """Reload the ``config`` module so environment changes take effect."""

    existing_module = sys.modules.get("config")
    if existing_module is None:
        return importlib.import_module("config")
    return importlib.reload(existing_module)


def clear_core_config_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove the core config environment variables used by these tests."""

    for variable_name in [
        "FLASK_ENV",
        "SECRET_KEY",
        "STRIPE_SECRET_KEY",
        "STRIPE_WEBHOOK_SECRET",
        "STRIPE_PUBLIC_BASE_URL",
        "RATELIMIT_STORAGE_URI",
        "ADMIN_USERNAME",
        "ADMIN_PASSWORD",
        "PUBLIC_SITE_PASSWORD_HASH",
    ]:
        monkeypatch.delenv(variable_name, raising=False)


def test_config_defaults_rate_limit_storage_to_memory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Use in-memory limiter storage by default in local development."""

    clear_core_config_env(monkeypatch)

    config_module = reload_config_module()

    assert config_module.RATELIMIT_STORAGE_URI == "memory://"


def test_config_requires_rate_limit_storage_uri_in_production(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fail fast in production if the shared limiter backend is missing."""

    clear_core_config_env(monkeypatch)
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "secret")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_123")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_123")
    monkeypatch.setenv("STRIPE_PUBLIC_BASE_URL", "https://example.com")
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "password")
    monkeypatch.setenv("PUBLIC_SITE_PASSWORD_HASH", "hash")

    with pytest.raises(RuntimeError, match="RATELIMIT_STORAGE_URI"):
        reload_config_module()

    clear_core_config_env(monkeypatch)
    reload_config_module()
