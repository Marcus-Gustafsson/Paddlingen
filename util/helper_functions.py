# util/helper_functions.py

import os
import random
from flask import current_app

app = current_app

def get_images_for_year(year: str) -> list[str]:
    """
    Return a random subset of image filenames from the given year's folder.

    This function:
      1. Looks inside 'static/images/<year>/' for files.
      2. Filters to only common image extensions.
      3. Shuffles the list randomly on each call.
      4. Returns up to 27 filenames, but never more than two rows of 9:
         - If fewer than 18 images total, returns up to 9.
         - If between 18 and 26 images, returns up to 18.
         - Otherwise returns exactly 27.

    Args:
        year (str): Folder name under static/images (e.g. "2024" or "2019_&_tidigare").

    Returns:
        list[str]: List of image filenames (not full paths), ready for
                   url_for('static', filename=f'images/{year}/<filename>').
    """
    # Build the absolute filesystem path to the year's image folder
    # current_app.root_path is the root directory of your Flask app
    img_folder = os.path.join(
        current_app.root_path,
        'static',
        'images',
        year
    )
    # Debug print (only in debug mode)
    if app.debug:
        print("DEBUG: Looking for images in:", img_folder)

    # Try to list all files in that directory. If it doesn't exist, use an empty list.
    try:
        all_files = os.listdir(img_folder)
    except FileNotFoundError:
        all_files = []

    # Define which file extensions we consider "images"
    valid_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.webp')

    # Filter out any filenames that don't end in a valid image extension
    image_files = [
        fname for fname in all_files
        if fname.lower().endswith(valid_extensions)
    ]

    # Shuffle in place so each page load shows a different random order
    random.shuffle(image_files)

    # Determine how many images to return:
    # - If fewer than 18 total images, return up to 9
    # - If 18–26 images, return up to 18
    # - If 27 or more, return exactly 27
    total = len(image_files)
    if total < 18:
        max_count = 9
    elif total < 27:
        max_count = 18
    else:
        max_count = 27

    # Slice the shuffled list to the desired length
    chosen = image_files[:max_count]

    return chosen