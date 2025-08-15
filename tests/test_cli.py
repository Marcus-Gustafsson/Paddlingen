"""Tests for custom Flask command line interface commands."""

import pytest
from app import db, User


def test_init_db_command_resets_tables(client):
    """Invoke ``flask init-db`` and ensure tables are recreated.

    The application seeds one admin user in the database. After running the
    ``init-db`` command all tables should be dropped and recreated, leaving the
    ``User`` table empty. This proves developers can start with a clean slate.

    Args:
        client (FlaskClient): Fixture providing a Flask test client.

    Returns:
        None: Assertions check that the database was cleared.

    """
    with client.application.app_context():
        assert User.query.count() == 1

    runner = client.application.test_cli_runner()
    with client.application.app_context():
        result = runner.invoke(args=['init-db'])
        assert 'Initialized the database.' in result.output
        assert User.query.count() == 0


def test_seed_admin_command_creates_user(client, monkeypatch):
    """Invoke ``flask seed-admin`` to add a new administrator.

    The command reads credentials from environment variables. The test sets
    these variables, runs the command and checks that a user with the given
    username now exists in the database.

    Args:
        client (FlaskClient): Fixture providing a Flask test client.
        monkeypatch (pytest.MonkeyPatch): Utility to set environment variables.

    Returns:
        None: Assertions verify the creation of the admin user.

    """
    runner = client.application.test_cli_runner()
    monkeypatch.setenv('ADMIN_USERNAME', 'cliadmin')
    monkeypatch.setenv('ADMIN_PASSWORD', 'secret')

    with client.application.app_context():
        result = runner.invoke(args=['seed-admin'])
        assert "Created admin 'cliadmin'." in result.output
        assert User.query.filter_by(username='cliadmin').first() is not None


def test_seed_admin_command_requires_env_vars(client, monkeypatch):
    """Ensure ``seed-admin`` fails when credentials are missing.

    If ``ADMIN_USERNAME`` or ``ADMIN_PASSWORD`` is absent the command should
    abort with an error message. This prevents accidental creation of accounts
    with empty credentials.

    Args:
        client (FlaskClient): Fixture providing a Flask test client.
        monkeypatch (pytest.MonkeyPatch): Used to clear environment variables.

    Returns:
        None: Assertions confirm the command fails and prints a helpful message.

    """
    runner = client.application.test_cli_runner()
    monkeypatch.delenv('ADMIN_USERNAME', raising=False)
    monkeypatch.delenv('ADMIN_PASSWORD', raising=False)

    with client.application.app_context():
        result = runner.invoke(args=['seed-admin'])
        assert result.exit_code != 0
        assert 'ADMIN_USERNAME and ADMIN_PASSWORD environment variables are required' in result.output
