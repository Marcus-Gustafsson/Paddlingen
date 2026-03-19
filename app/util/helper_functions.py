"""Utility helpers used across the application."""

from pathlib import Path

from flask import current_app


def get_previous_year_image_filenames() -> list[str]:
    """Return the flattened previous-years gallery image filenames.

    The homepage ribbon and gallery now read from one shared folder:
    ``static/images/previous_years/``.

    Duplicate filenames from the old year-based folders were renamed during the
    refactor, usually by adding a year prefix, so the flattened folder can be
    read safely without collisions.

    Returns:
        list[str]: Sorted image filenames ready for
        ``url_for('static', filename='images/previous_years/<filename>')``.
    """
    static_folder = current_app.static_folder
    if static_folder is None:
        raise RuntimeError("Static folder is not configured")

    image_folder = Path(static_folder) / "images" / "previous_years"

    if current_app.debug:
        print("DEBUG: Looking for previous-year images in:", image_folder)

    valid_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
    image_files = [
        image_path.name
        for image_path in image_folder.iterdir()
        if image_path.is_file() and image_path.suffix.lower() in valid_extensions
    ]

    return sorted(image_files)
