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
# File: app/routes.py   (or wherever your Blueprint is defined)

import os
import random
from flask import Blueprint, render_template, current_app

main = Blueprint('main', __name__)

@main.route("/")  # The homepage
def index():
    """
    1) Read all image filenames from the 'static/images/2024/' folder.
    2) Randomly shuffle them.
    3) Take at most 18 (9 per row × 2 rows) so the CSS grid never has more than two rows.
    4) Repeat the same logic for 2023 if desired.
    5) Render index.html with pics2024 (and pics2023).
    """

    # 1. Build the absolute path to your '2024' folder inside static
    #    current_app.root_path is the filesystem path to your Flask app package
    folder_2024 = os.path.join(current_app.root_path, 'static', 'images', '2024')
    folder_2023 = os.path.join(current_app.root_path, 'static', 'images', '2023')
    folder_2022 = os.path.join(current_app.root_path, 'static', 'images', '2022')

    # 2. List all files in those directories (only filenames, not full paths)
    try:
        all_files_2024 = os.listdir(folder_2024)
    except FileNotFoundError:
        all_files_2024 = []  # in case the folder doesn't exist yet
    
    try:
        all_files_2023 = os.listdir(folder_2023)
    except FileNotFoundError:
        all_files_2023 = []

    try:
        all_files_2022 = os.listdir(folder_2022)
    except FileNotFoundError:
        all_files_2022 = []

    # 3. Filter out any non‐image files if needed (optional; assume everything in this folder is an image)
    #    For example, keep only .jpg/.png/.jpeg/.gif (simple approach):
    valid_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.webp')
    images_2024 = [fname for fname in all_files_2024 if fname.lower().endswith(valid_extensions)]
    images_2023 = [fname for fname in all_files_2023 if fname.lower().endswith(valid_extensions)]
    images_2022 = [fname for fname in all_files_2022 if fname.lower().endswith(valid_extensions)]

    # 4. Shuffle the lists in place so that each page load picks random images
    random.shuffle(images_2024)
    random.shuffle(images_2023)
    random.shuffle(images_2022)

    # 5. Take at most 9,18 or 27 filenames from each year (1/2/3 rows × 9 columns)

    if len(images_2024) < 18:
        pics2024 = images_2024[:9]
    elif len(images_2024) < 27:
        pics2024 = images_2024[:18]
    else:
        pics2024 = images_2024[:27]

    if len(images_2023) < 18:
        pics2023 = images_2023[:9]
    elif len(images_2023) < 27:
        pics2023 = images_2023[:18]
    else:
        pics2023 = images_2023[:27]

    print("DBG: len(images_2022) = ", len(images_2022))

    if len(images_2022) < 18:
        pics2022 = images_2022[:9]
    elif len(images_2022) < 27:
        pics2022 = images_2022[:18]
    else:
        pics2022 = images_2022[:27]




    # 6. Pass them into the template. Jinja will loop over each list to build the grid.
    return render_template("index.html",
                           pics2024=pics2024,
                           pics2023=pics2023,
                           pics2022=pics2022)



