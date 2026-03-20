"""Utility helpers used across the application."""

from __future__ import annotations

import json
import re
from pathlib import Path

from flask import current_app

VALID_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
IMAGE_ID_PATTERN = re.compile(r"IMG-(\d{4})$")


def get_project_root_from_static_folder(static_folder: str | Path) -> Path:
    """Return the repository root based on the configured static folder."""

    return Path(static_folder).resolve().parent


def get_previous_year_image_folder(project_root: Path) -> Path:
    """Return the directory that stores the previous-years image files."""

    return project_root / "static" / "images" / "previous_years"


def get_previous_year_image_metadata_path(project_root: Path) -> Path:
    """Return the JSON file that stores stable image metadata."""

    return project_root / "data" / "previous_year_images.json"


def get_previous_year_ribbon_variant_folder(project_root: Path) -> Path:
    """Return the directory that stores optimized ribbon image variants."""

    return get_previous_year_image_folder(project_root) / "ribbon"


def get_previous_year_gallery_variant_folder(project_root: Path) -> Path:
    """Return the directory that stores optimized gallery image variants."""

    return get_previous_year_image_folder(project_root) / "gallery"


def get_previous_year_variant_filename(image_id: str) -> str:
    """Return the generated variant filename for one stable image ID."""

    return f"{image_id}.webp"


def list_previous_year_image_filenames(image_folder: Path) -> list[str]:
    """Return valid previous-years image filenames from the image folder."""

    return sorted(
        image_path.name
        for image_path in image_folder.iterdir()
        if image_path.is_file() and image_path.suffix.lower() in VALID_IMAGE_EXTENSIONS
    )


def load_previous_year_image_metadata_file(
    metadata_path: Path,
) -> list[dict[str, str]]:
    """Load the raw image metadata JSON file if it exists."""

    if not metadata_path.exists():
        return []

    with metadata_path.open(encoding="utf-8") as metadata_file:
        loaded_data = json.load(metadata_file)

    if not isinstance(loaded_data, list):
        raise ValueError("Image metadata file must contain a list of objects.")

    metadata_entries: list[dict[str, str]] = []
    for metadata_entry in loaded_data:
        if not isinstance(metadata_entry, dict):
            continue

        image_id = metadata_entry.get("id")
        filename = metadata_entry.get("filename")
        if isinstance(image_id, str) and isinstance(filename, str):
            metadata_entries.append({"id": image_id, "filename": filename})

    return metadata_entries


def build_previous_year_image_metadata(
    image_filenames: list[str], existing_metadata: list[dict[str, str]]
) -> list[dict[str, str]]:
    """Return metadata with stable image IDs for the current filenames.

    Existing IDs are preserved for filenames already present in the metadata
    file. New filenames are assigned the next available `IMG-000x` value.
    """

    image_id_by_filename: dict[str, str] = {}
    highest_image_number = 0

    for metadata_entry in existing_metadata:
        image_id = metadata_entry.get("id", "")
        filename = metadata_entry.get("filename", "")
        image_id_match = IMAGE_ID_PATTERN.fullmatch(image_id)
        if not image_id_match or not filename:
            continue

        if filename not in image_id_by_filename:
            image_id_by_filename[filename] = image_id
            highest_image_number = max(highest_image_number, int(image_id_match[1]))

    synchronized_metadata: list[dict[str, str]] = []
    for filename in image_filenames:
        preserved_image_id = image_id_by_filename.get(filename)
        if preserved_image_id is None:
            highest_image_number += 1
            preserved_image_id = f"IMG-{highest_image_number:04d}"

        synchronized_metadata.append({"id": preserved_image_id, "filename": filename})

    return synchronized_metadata


def write_previous_year_image_metadata_file(
    metadata_path: Path, metadata_entries: list[dict[str, str]]
) -> None:
    """Write the synchronized image metadata to disk."""

    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with metadata_path.open("w", encoding="utf-8") as metadata_file:
        json.dump(metadata_entries, metadata_file, ensure_ascii=False, indent=2)
        metadata_file.write("\n")


def get_previous_year_image_metadata() -> list[dict[str, str]]:
    """Return stable metadata for the flattened previous-years image folder.

    The current gallery relies on one shared metadata file so each image can
    keep a stable public ID even if files are reordered later.
    """

    static_folder = current_app.static_folder
    if static_folder is None:
        raise RuntimeError("Static folder is not configured")

    project_root = get_project_root_from_static_folder(static_folder)
    image_folder = get_previous_year_image_folder(project_root)
    metadata_path = get_previous_year_image_metadata_path(project_root)

    image_filenames = list_previous_year_image_filenames(image_folder)
    existing_metadata = load_previous_year_image_metadata_file(metadata_path)
    synchronized_metadata = build_previous_year_image_metadata(
        image_filenames, existing_metadata
    )

    if synchronized_metadata != existing_metadata:
        current_app.logger.warning(
            "Previous-years image metadata is missing or out of sync. "
            "Run `uv run python scripts/sync_previous_year_image_metadata.py` "
            "to update data/previous_year_images.json."
        )

    return synchronized_metadata


def get_previous_year_image_filenames() -> list[str]:
    """Return the flattened previous-years gallery image filenames."""

    return [
        metadata_entry["filename"]
        for metadata_entry in get_previous_year_image_metadata()
    ]
