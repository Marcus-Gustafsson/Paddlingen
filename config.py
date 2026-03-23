"""
File: config.py

What it does:
  - This file holds all the important settings for our Flask application.
  - It keeps configuration separate from our main application logic, which is a
    very good practice. This includes things like database location, debug modes,
    and secret keys.
  - When ``FLASK_ENV`` is set to ``"production"`` the module checks that all
    required credentials are provided.  Missing values raise an immediate and error so deployments fail.

Why it’s here:
  - By centralizing configuration, we can easily change settings for different
    environments (like development vs. production) without changing the core
    application code.
"""

import os
from datetime import datetime
from dotenv import load_dotenv

# --- Loading Environment Variables ---
# The next two lines are for loading "secrets" from a special file named `.env`.
# This `.env` file should NOT be shared publicly (e.g., on GitHub).
# It's where you'll store sensitive information like secret keys and passwords.

load_dotenv(override=False)


# Helper -------------------------------------------------------------
def _bool_from_env(name: str, default: bool = False) -> bool:
    """Return a boolean value read from an environment variable.

    This helper normalizes common truthy strings ("1", "true", "yes", etc.)
    and falls back to ``default`` when the variable is missing.  It keeps
    configuration parsing tidy and easy to understand for newcomers.

    Args:
        name (str): The environment variable to read.
        default (bool, optional): Value to return if the variable is unset.
            Defaults to ``False``.

    Returns:
        bool: ``True`` when the variable contains a truthy string,
        otherwise ``False`` or the provided default.
    """

    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "t", "yes", "y", "on"}


def _format_swedish_date_display(iso_date: str, include_year: bool = False) -> str:
    """Return a simple Swedish date string for a YYYY-MM-DD date.

    Args:
        iso_date (str): Date in ``YYYY-MM-DD`` format.
        include_year (bool, optional): Whether the returned string should
            include the year. Defaults to ``False``.

    Returns:
        str: Date formatted like ``"28 juni"`` or ``"28 juni 2026"``.
    """

    month_names = {
        1: "januari",
        2: "februari",
        3: "mars",
        4: "april",
        5: "maj",
        6: "juni",
        7: "juli",
        8: "augusti",
        9: "september",
        10: "oktober",
        11: "november",
        12: "december",
    }
    parsed_date = datetime.strptime(iso_date, "%Y-%m-%d")
    base_display = f"{parsed_date.day} {month_names[parsed_date.month]}"
    if include_year:
        return f"{base_display} {parsed_date.year}"
    return base_display


# --- Event Settings ---
#
# Keep the most important event-specific values here so they are easy to find
# and update before each year's booking period.
EVENT_DATE_ISO = "2026-03-20"
EVENT_YEAR = datetime.strptime(EVENT_DATE_ISO, "%Y-%m-%d").year
EVENT_TIME_24H = "10:00"
EVENT_DATETIME_LOCAL_ISO = f"{EVENT_DATE_ISO}T{EVENT_TIME_24H}:00"
EVENT_DATE_DISPLAY = _format_swedish_date_display(EVENT_DATE_ISO)
EVENT_FULL_DATE_DISPLAY = _format_swedish_date_display(
    EVENT_DATE_ISO, include_year=True
)
EVENT_TIME_DISPLAY = f"Kl {EVENT_TIME_24H}"
EVENT_TITLE = "Paddlingen"
EVENT_SUBTITLE = '"Bästa dagen på hela året!" - Mathias Axelsson'
EVENT_TAGLINE = EVENT_SUBTITLE
EVENT_STARTING_LOCATION_NAME = "Havsjömossen"
EVENT_STARTING_LOCATION_URL = (
    "https://www.google.com/maps/dir/Kopparberg/Havsjomossen,+714+92+Kopparberg/"
    "@59.8803129,14.8725218,12.45z/data=!4m14!4m13!1m5!1m1!"
    "1s0x465da83f08095abd:0x5881b6deffa02146!2m2!1d15.00051!2d59.87549!"
    "1m5!1m1!1s0x465d07135a643b4d:0xd9ffac76e697a6b5!2m2!1d14.8500001!"
    "2d59.8666667!3e0?entry=ttu"
)
EVENT_LOCATION_NAME = EVENT_STARTING_LOCATION_NAME
EVENT_LOCATION_URL = EVENT_STARTING_LOCATION_URL
EVENT_END_LOCATION_NAME = "Havsjömossen"
EVENT_END_LOCATION_URL = EVENT_STARTING_LOCATION_URL
EVENT_LATITUDE = 59.866580523479584
EVENT_LONGITUDE = 14.850996977247622
WEATHER_FORECAST_DAYS_BEFORE_EVENT = 7


# Total number of canoes available for booking this year and price per canoe.
AVAILABLE_CANOES = 50
MAX_CANOES_PER_BOOKING = 5
CANOE_PRICE_SEK = 1200
CONTACT_EMAIL = "info@paddlingen.se"
CONTACT_PHONE = "012-345 6789"
FAQ_BOOKING_TEXT = f"""
Hur många kanoter finns? Max {AVAILABLE_CANOES} stycken, först till kvarn.
Hur många kanoter per bokning? Du kan boka upp till {MAX_CANOES_PER_BOOKING} kanoter åt gången.
Kan jag boka åt någon annan? Ja, ange förnamn och efternamn för varje deltagare i bokningen.
""".strip()
FAQ_CHANGES_AND_QUESTIONS_TEXT = """
Avbokning: Senast 7 dagar före eventet.
Behöver du hjälp? Använd kontaktfönstret för att hitta e-post och telefon.
""".strip()
RULES_ON_THE_WATER_TEXT = """
Var rädd om kanoterna och följ instruktionerna från arrangören.
Max två personer per kanot om inget annat meddelas på plats.
Håll avstånd till andra kanoter och visa hänsyn vid start och landning.
""".strip()
RULES_AFTER_PADDLING_TEXT = """
Lämna tillbaka utrustningen där arrangören visar.
Ta med skräp och lämna området i gott skick.
Fråga hellre en gång extra än att chansa om något känns oklart.
""".strip()


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
PUBLIC_SITE_PASSWORD_HASH = os.getenv("PUBLIC_SITE_PASSWORD_HASH")

# In production all of the above values must be defined.
# The variables must be set in ``.env`` or the hosting environment.
if os.getenv("FLASK_ENV") == "production":
    _missing: list[str] = [
        name
        for name, value in {
            "SECRET_KEY": SECRET_KEY,
            "PAYMENT_API_KEY": PAYMENT_API_KEY,
            "ADMIN_USERNAME": ADMIN_USERNAME,
            "ADMIN_PASSWORD": ADMIN_PASSWORD,
            "PUBLIC_SITE_PASSWORD_HASH": PUBLIC_SITE_PASSWORD_HASH,
        }.items()
        if not value
    ]
    if _missing:
        joined = ", ".join(_missing)
        raise RuntimeError(
            "Missing required environment variable(s): "
            f"{joined}. Create a '.env' file (see '.env.example') "
            "or set them in your shell before starting the server."
        )


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
    SQLALCHEMY_DATABASE_URI = (
        f"sqlite:///{os.path.join(BASE_DIR, 'instance/paddlingen.db')}"
    )

# This turns off a feature of Flask-SQLAlchemy that we don't need.
# It tracks modifications to objects and emits signals, which can use extra memory.
# Disabling it is a common practice and helps avoid a deprecation warning.
SQLALCHEMY_TRACK_MODIFICATIONS = False

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
SESSION_COOKIE_SAMESITE = "Lax"

# Reverse-proxy header trust should stay disabled by default.
# Enable this in a controlled deployment behind a trusted proxy such as
# Coolify/Traefik so Flask reads the original HTTPS scheme and client IP.
TRUST_REVERSE_PROXY_HEADERS = _bool_from_env(
    "TRUST_REVERSE_PROXY_HEADERS", default=False
)


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
