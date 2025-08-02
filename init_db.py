#!/usr/bin/env python3
"""
init_db.py

– Deletes the old SQLite file
– Re‐creates all tables
– Inserts one admin User with credentials from your environment

Logging is used instead of print statements so that output can be
easily controlled or redirected. The main application configures the
logging system; here we simply grab a module-level logger.
"""

import os
import logging
from main import app, db, User

# ---------------------------------------------------------------------------
# LOGGING SETUP
# ---------------------------------------------------------------------------
# We get a logger for this module. The configuration (log level, format, etc.)
# is defined in main.py. Using a logger instead of print makes it simple to
# adjust verbosity and to integrate with other logging handlers.
logger = logging.getLogger(__name__)

DB_PATH = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    'instance',
    'paddlingen.db'
)

def init_db():
    """Delete the old DB file (if any) and create fresh tables.

    The function reports its progress using ``logger.info`` so you can see
    what is happening when the script runs.
    """
    # Ensure the instance directory exists before touching the database file
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        logger.info("Removed old database file at %s.", DB_PATH)

    with app.app_context():
        db.create_all()
        logger.info("Created new database schema at %s.", DB_PATH)

def seed_admin():
    """Insert the initial admin user (if none exists).

    ``logger.debug`` shows the loaded credentials when the logging level is
    DEBUG, while ``logger.info`` records general progress messages.
    """
    with app.app_context():
        # Read credentials from environment (.env)
        admin_user = os.getenv("ADMIN_USERNAME")
        admin_pass = os.getenv("ADMIN_PASSWORD")

        # Helpful debug logs if you need to verify the loaded credentials.
        logger.debug("Admin username from environment: %s", admin_user)
        logger.debug("Admin password from environment: %s", admin_pass)

        # Don't duplicate if already there
        if User.query.filter_by(username=admin_user).first():
            logger.info("Admin '%s' already exists—skipping.", admin_user)
            return

        u = User(username=admin_user)
        u.set_password(admin_pass)
        db.session.add(u)
        db.session.commit()
        logger.info("Created admin user '%s'.", admin_user)

if __name__ == '__main__':
    init_db()
    seed_admin()
