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
load_dotenv()

# Now we can safely read our secrets
SECRET_KEY = os.getenv("SECRET_KEY")
PAYMENT_API_KEY = os.getenv("PAYMENT_API_KEY")

# Database in instance/paddlingen.sqlite (we’ll set this up later)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SQLALCHEMY_DATABASE_URI = 'sqlite:///paddlingen.db'
print(os.path.join(BASE_DIR, 'instance/paddlingen.db'))
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Debug mode on for local testing
DEBUG = True

