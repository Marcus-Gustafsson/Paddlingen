"""WSGI entry point for production servers.

This module exposes a variable named :data:`application` so that WSGI
servers (Gunicorn, uWSGI, etc.) can run the Flask app created by
:func:`app.create_app`.
"""

from app import create_app

application = create_app()
