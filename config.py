"""
File: config.py

What it does:
  - Holds configuration settings (database path, debug on/off).
  - Keeps secret stuff (later you can add API keys here).

Why it’s here:
  - Flask can load all settings before the app starts.

"""

import os
from dotenv import load_dotenv

# Load local .env (only in development)
load_dotenv(override=True)

# Now we can safely read our secrets
SECRET_KEY = os.getenv("SECRET_KEY")
PAYMENT_API_KEY = os.getenv("PAYMENT_API_KEY")

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# Database in instance/paddlingen.sqlite (we’ll set this up later)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SQLALCHEMY_DATABASE_URI = 'sqlite:///paddlingen.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False


# Enable CSRF globally for all “POST” endpoints
WTF_CSRF_ENABLED      = True
# Secret key used to sign CSRF tokens
WTF_CSRF_SECRET_KEY   = SECRET_KEY

# Debug mode on for local testing
DEBUG = True

