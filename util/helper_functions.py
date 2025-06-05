
import os, random
from flask import current_app

def get_images_for_year(year = str):


    """
    1) Read all image filenames from the 'static/images/2024/' folder.
    2) Randomly shuffle them.
    3) Take at most 18 (9 per row × 2 rows) so the CSS grid never has more than two rows.
    4) Repeat the same logic for 2023 if desired.
    5) Render index.html with pics2024 (and pics2023).
    """

    # 1. Build the absolute path to your '2024' folder inside static
    #    current_app.root_path is the filesystem path to your Flask app package
    img_folder = os.path.join(current_app.root_path, 'static', 'images', year)
    print("DBG: img_folder = ", img_folder)

    # 2. List all files in those directories (only filenames, not full paths)
    try:
        all_img_files = os.listdir(img_folder)
    except FileNotFoundError:
        all_img_files = []  # in case the folder doesn't exist yet

    # 3. Filter out any non‐image files if needed (optional; assume everything in this folder is an image)
    #    For example, keep only .jpg/.png/.jpeg/.gif (simple approach):
    valid_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.webp')
    valid_images = []
    valid_images = [full_name for full_name in all_img_files if full_name.lower().endswith(valid_extensions)]

    # 4. Shuffle the lists in place so that each page load picks random images
    random.shuffle(valid_images)

    # 5. Take at most 9,18 or 27 filenames from each year (1/2/3 rows × 9 columns)

    if len(valid_images) < 18:
        chosen_pictures = valid_images[:9]
    elif len(valid_images) < 27:
        chosen_pictures = valid_images[:18]
    else:
        chosen_pictures = valid_images[:27]

    return chosen_pictures