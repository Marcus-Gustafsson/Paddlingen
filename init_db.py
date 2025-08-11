#!/usr/bin/env python3
"""Convenience wrapper around the database management CLI commands.

The real work of creating tables and seeding an administrator account is
performed by custom `flask` command line interface (CLI) commands
registered inside :mod:`app.__init__`.  Developers are encouraged to run
those commands directly:

    flask --app app init-db
    flask --app app seed-admin

Running this script simply executes both commands in sequence.  It is
provided mainly for quick experiments or for environments where invoking
the Flask CLI is inconvenient.
"""

from app import create_app, init_db_command, seed_admin_command

# Build the application so that the CLI command functions have access to
# the configured extensions (database, etc.).
flask_application = create_app()


if __name__ == "__main__":
    # The command functions expect an application context in order to
    # interact with the database.  We create that context here and call
    # the commands directly.
    with flask_application.app_context():
        init_db_command()
        seed_admin_command()
