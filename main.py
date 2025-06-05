"""
File: run.py

What it does:
  - The “entry point” of your app.
  - When you run “python run.py”, this file creates and starts the server.

Why it’s here:
  - It lives at the project root so it’s easy to find and run.

"""


"""
The ‘entry point’ to start your site.
Run with: python run.py
"""

import os
import random
from util.helper_functions import get_images_for_year
from flask import Flask, render_template

app = Flask(__name__)    # Create a new Flask web app
app.config.from_pyfile('config.py')  # Load settings


@app.route("/")  # The homepage
def index():

    # 6. Pass them into the template. Jinja will loop over each list to build the grid.
    return render_template("index.html",
                           pics2024=get_images_for_year("2024"),
                           pics2023=get_images_for_year("2023"),
                           pics2022=get_images_for_year("2022"))

if __name__ == "__main__":
    app.run()   # Starts Flask on http://127.0.0.1:5000

