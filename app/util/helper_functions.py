"""Utility helpers used across the application."""

import os
import random
from flask import current_app


def get_images_for_year(year: str) -> list[str]:
    """Return a random subset of image filenames for the given year.

    The function searches inside ``static/images/<year>/`` for image files,
    shuffles them, and returns at most 27 filenames.  The number of files is
    capped so the gallery in the template never becomes overwhelming.

    Args:
        year: Folder name under ``static/images`` such as ``"2024"`` or
            ``"2019_&_tidigare"``.

    Returns:
        A list of image filenames (not full paths) ready for
        ``url_for('static', filename=f'images/{year}/<filename>')``.
    """
    image_folder = os.path.join(
        current_app.static_folder,
        "images",
        year,
    )

    # Debug print (only when Flask is in debug mode)
    if current_app.debug:
        print("DEBUG: Looking for images in:", image_folder)

    try:
        all_files = os.listdir(image_folder)
    except FileNotFoundError:
        all_files = []

    valid_extensions = (".png", ".jpg", ".jpeg", ".gif", ".webp")
    image_files = [
        file_name
        for file_name in all_files
        if file_name.lower().endswith(valid_extensions)
    ]

    random.shuffle(image_files)

    total_images = len(image_files)
    if total_images < 18:
        maximum_count = 9
    elif total_images < 27:
        maximum_count = 18
    else:
        maximum_count = 27

    selected_images = image_files[:maximum_count]
    return selected_images
