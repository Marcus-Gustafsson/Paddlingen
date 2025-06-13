#!/usr/bin/env python3
"""
init_db.py

– Deletes the old SQLite file
– Re‐creates all tables
– Inserts one admin User with credentials from your environment
"""

import os
from main import app, db, User

DB_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'paddlingen.db')

def init_db():
    """Delete the old DB file (if any) and create fresh tables."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("Removed old database file.")
    with app.app_context():
        db.create_all()
        print("Created new database schema.")

def seed_admin():
    """Insert the initial admin user (if none exists)."""
    with app.app_context():
        # Read credentials from environment (.env)
        admin_user = os.getenv("ADMIN_USERNAME")
        admin_pass = os.getenv("ADMIN_PASSWORD")
        print("DBG: admin_user = ", admin_user)
        print("DBG: admin_pass = ", admin_pass)
        
        # Don't duplicate if already there
        if User.query.filter_by(username=admin_user).first():
            print(f"Admin '{admin_user}' already exists—skipping.")
            return
        
        u = User(username=admin_user)
        u.set_password(admin_pass)
        db.session.add(u)
        db.session.commit()
        print(f"Created admin user '{admin_user}'.")

if __name__ == '__main__':
    init_db()
    seed_admin()