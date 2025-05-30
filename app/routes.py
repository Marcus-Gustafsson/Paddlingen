"""
File: app/routes.py

What it does:
  - Defines which URL goes to which page or function.
  - For example: “/” shows index.html, “/book” handles booking submissions.

Why it’s here:
  - Separates the web-page logic from the database and setup code.
"""

"""
Defines which URLs show which pages.
"""
from flask import Blueprint, render_template

main = Blueprint('main', __name__)

@main.route("/")  # When the user goes to http://localhost:5000/
def index():
    # Render the index.html template we placed in app/templates/
    return render_template("index.html")

