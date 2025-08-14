"""
File: config.py

What it does:
  - This file holds all the important settings for our Flask application.
  - It keeps configuration separate from our main application logic, which is a
    very good practice. This includes things like database location, debug modes,
    and secret keys.

Why it’s here:
  - By centralizing configuration, we can easily change settings for different
    environments (like development vs. production) without changing the core
    application code.
"""

import os
from dotenv import load_dotenv

# --- Loading Environment Variables ---
# The next two lines are for loading "secrets" from a special file named `.env`.
# This `.env` file should NOT be shared publicly (e.g., on GitHub).
# It's where you'll store sensitive information like secret keys and passwords.

load_dotenv(override=True)

# Helper -------------------------------------------------------------
def _bool_from_env(name: str, default: bool = False) -> bool:
    """Return a boolean value from an environment variable.

    This lets us control configuration with environment variables (like in a
    `.env` file) without editing the code. If the variable is missing we fall
    back to the provided default.
    """
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "t", "yes", "y", "on"}


# --- Secret Keys & Credentials ---
# These are loaded from your .env file for security.

# A long, random, and secret string of characters.
# Flask uses this to "sign" and secure session cookies and other security-related
# data. Think of it as a master password for the application's security features.
# It must be kept secret!
SECRET_KEY = os.getenv("SECRET_KEY")

# An example of another secret you might need. If you integrate with a payment
# service like Stripe or PayPal, they will give you an API key. You would store it
# here, loaded safely from your .env file.
PAYMENT_API_KEY = os.getenv("PAYMENT_API_KEY")

# Credentials for creating the first administrator account.
# Storing them here is a simple way to get started. In a larger application,
# you might create the first admin using a separate command-line script.
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")


# --- Database Configuration ---

# This line finds the absolute path of the directory where this config.py file lives.
# Using an absolute path is more reliable than a relative one.
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# This tells our database library (Flask-SQLAlchemy) where to find the database.
#
# The URI can come from the ``DATABASE_URL`` environment variable.  This allows
# production deployments to point at a managed database service such as
# PostgreSQL.  A typical PostgreSQL URI looks like::
#
#     postgresql+psycopg://user:password@hostname:5432/databasename
#
# If ``DATABASE_URL`` is not defined we fall back to a SQLite file stored in the
# repository's ``instance`` directory.  SQLite requires no separate server and is
# perfect for local development.
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
else:
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'instance/paddlingen.db')}"

# This turns off a feature of Flask-SQLAlchemy that we don't need.
# It tracks modifications to objects and emits signals, which can use extra memory.
# Disabling it is a common practice and helps avoid a deprecation warning.
SQLALCHEMY_TRACK_MODIFICATIONS = False

# config.py
MAX_CANOEES = 50


# --- Form & CSRF Protection Configuration (Flask-WTF) ---

# This globally enables CSRF (Cross-Site Request Forgery) protection for all forms.
# It's a critical security feature that prevents other malicious websites from
# tricking your users into submitting data to your app without their knowledge.
WTF_CSRF_ENABLED = True

# Flask-WTF uses this key to generate and validate secure CSRF tokens.
# We can simply reuse our main SECRET_KEY for this purpose.
WTF_CSRF_SECRET_KEY = SECRET_KEY


# --- Session Cookie Security Settings ---
# These settings make our user login sessions more secure.

# If set to True, the browser will only send the session cookie over a secure
# HTTPS connection. This prevents the cookie from being stolen by eavesdroppers
# on an insecure network (like public Wi-Fi).
#
# We default this to True so production deployments are safe by default.
# When developing locally without HTTPS, set `SESSION_COOKIE_SECURE=False`
# in your environment (e.g. in `.env`) to allow testing over plain HTTP.
SESSION_COOKIE_SECURE = _bool_from_env("SESSION_COOKIE_SECURE", default=True)

# If set to True, it tells the browser not to allow JavaScript to access the
# session cookie. This is a crucial defense against Cross-Site Scripting (XSS)
# attacks where an attacker might try to steal the cookie using malicious script.
SESSION_COOKIE_HTTPONLY = True

# This is another modern security measure to mitigate CSRF attacks.
# 'Lax' means the cookie will be sent when a user navigates to our site from
# an external link, but not on requests initiated by third-party sites (like
# images or forms). 'Strict' is more secure but can be less user-friendly.
# 'Lax' is a great, secure default.
SESSION_COOKIE_SAMESITE = 'Lax'



# --- Development Settings ---

# The DEBUG flag enables or disables Flask's debug mode.
# When True:
#   - The server will automatically reload when you change your code.
#   - It will show a detailed, interactive debugger in the browser if an error occurs.
# WARNING: This MUST be set to `False` in a production environment, as the
# interactive debugger can expose sensitive information.
#
# The setting defaults to False for safety. To enable the debugger during
# development, export `FLASK_DEBUG=True` or add it to your `.env` file.
DEBUG = _bool_from_env("FLASK_DEBUG", default=False)
