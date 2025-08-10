#!/usr/bin/env python3
"""Utility script to reset and seed the local SQLite database."""

import os
import logging
from app import create_app, db, User

# Application instance used for database operations
flask_application = create_app()

# ---------------------------------------------------------------------------
# LOGGING SETUP
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)

DATABASE_PATH = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    "instance",
    "paddlingen.db",
)


def init_db() -> None:
    """Delete the old database file (if any) and create fresh tables."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

    if os.path.exists(DATABASE_PATH):
        os.remove(DATABASE_PATH)
        logger.info("Removed old database file at %s.", DATABASE_PATH)

    with flask_application.app_context():
        db.create_all()
        logger.info("Created new database schema at %s.", DATABASE_PATH)


def seed_admin() -> None:
    """Insert the initial admin user if it is missing."""
    with flask_application.app_context():
        admin_username = os.getenv("ADMIN_USERNAME")
        admin_password = os.getenv("ADMIN_PASSWORD")

        logger.debug("Admin username from environment: %s", admin_username)
        logger.debug("Admin password from environment: %s", admin_password)

        if User.query.filter_by(username=admin_username).first():
            logger.info("Admin '%s' already exists—skipping.", admin_username)
            return

        admin_user_object = User(username=admin_username)
        admin_user_object.set_password(admin_password)
        db.session.add(admin_user_object)
        db.session.commit()
        logger.info("Created admin user '%s'.", admin_username)


if __name__ == "__main__":
    init_db()
    seed_admin()
