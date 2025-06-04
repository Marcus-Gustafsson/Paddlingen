"""
File: app/__init__.py

What it does:
  - Creates a new Flask web app.
  - Loads settings from config.py (like where our database lives).
  - Sets up the database connection (so we can save bookings).
  - Registers our “routes” so the app knows which pages to show.

Why it’s here:
  - Keeps all the app setup in one place, so routes and models stay clean.

"""



"""
Initializes the Flask app.
Sets up any extensions (e.g. database) here.
"""
from flask import Flask

def create_app():
    app = Flask(__name__)    # Create a new Flask web app
    app.config.from_pyfile('../config.py')  # Load settings

    # Register our routes
    from .routes import main
    app.register_blueprint(main)

    return app

