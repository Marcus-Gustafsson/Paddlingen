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
import os
from flask import Blueprint, render_template, current_app

main = Blueprint('main', __name__)

@main.route("/")
def index():
    # 1. Build absolute path to static/images/2024
    folder_2024 = os.path.join(current_app.static_folder, 'images', '2024')
    # 2. List only real files
    pics2024 = [f for f in os.listdir(folder_2024)
                if os.path.isfile(os.path.join(folder_2024, f))]
    # (Repeat for 2023 if you like)
    folder_2023 = os.path.join(current_app.static_folder, 'images', '2023')
    pics2023 = [f for f in os.listdir(folder_2023)
                if os.path.isfile(os.path.join(folder_2023, f))]

    # 3. Pass them into the template
    return render_template("index.html",
                           pics2024=pics2024,
                           pics2023=pics2023)


