"""Synchronize previous-years image metadata and generated image variants.

Run this script whenever files are added, removed, or renamed inside
`static/images/previous_years/`.
"""

from __future__ import annotations

from pathlib import Path
import sys

from PIL import Image, ImageOps

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

RIBBON_VARIANT_SIZE = (480, 320)
GALLERY_VARIANT_SIZE = (1600, 1600)
RIBBON_VARIANT_QUALITY = 78
GALLERY_VARIANT_QUALITY = 84


def create_webp_variant(
    source_image_path: Path,
    target_image_path: Path,
    variant_size: tuple[int, int],
    quality: int,
) -> None:
    """Create one optimized WebP variant from the source image.

    Args:
        source_image_path: Original image file from `static/images/previous_years/`.
        target_image_path: Generated variant output path.
        variant_size: Maximum width and height for the generated image.
        quality: WebP quality setting used when saving the file.
    """

    with Image.open(source_image_path) as opened_image:
        prepared_image = ImageOps.exif_transpose(opened_image)

        if prepared_image.mode not in {"RGB", "RGBA"}:
            prepared_image = prepared_image.convert("RGBA")

        contained_image = ImageOps.contain(prepared_image, variant_size)

        if contained_image.mode == "RGBA":
            contained_image.save(
                target_image_path,
                format="WEBP",
                quality=quality,
                method=6,
            )
            return

        contained_image.convert("RGB").save(
            target_image_path,
            format="WEBP",
            quality=quality,
            method=6,
        )


def remove_stale_variant_files(
    variant_folder: Path, expected_filenames: set[str]
) -> list[Path]:
    """Remove generated variant files that no longer match the metadata."""

    removed_files: list[Path] = []
    if not variant_folder.exists():
        return removed_files

    for variant_path in variant_folder.iterdir():
        if not variant_path.is_file():
            continue

        if variant_path.name not in expected_filenames:
            variant_path.unlink()
            removed_files.append(variant_path)

    return removed_files


def main() -> None:
    """Update metadata plus optimized ribbon and gallery image variants."""

    from app.util.helper_functions import (
        build_previous_year_image_metadata,
        get_previous_year_gallery_variant_folder,
        get_previous_year_image_folder,
        get_previous_year_image_metadata_path,
        get_previous_year_ribbon_variant_folder,
        get_previous_year_variant_filename,
        list_previous_year_image_filenames,
        load_previous_year_image_metadata_file,
        write_previous_year_image_metadata_file,
    )

    image_folder = get_previous_year_image_folder(PROJECT_ROOT)
    metadata_path = get_previous_year_image_metadata_path(PROJECT_ROOT)
    ribbon_variant_folder = get_previous_year_ribbon_variant_folder(PROJECT_ROOT)
    gallery_variant_folder = get_previous_year_gallery_variant_folder(PROJECT_ROOT)

    image_filenames = list_previous_year_image_filenames(image_folder)
    existing_metadata = load_previous_year_image_metadata_file(metadata_path)
    synchronized_metadata = build_previous_year_image_metadata(
        image_filenames, existing_metadata
    )

    write_previous_year_image_metadata_file(metadata_path, synchronized_metadata)

    ribbon_variant_folder.mkdir(parents=True, exist_ok=True)
    gallery_variant_folder.mkdir(parents=True, exist_ok=True)

    expected_variant_filenames = {
        get_previous_year_variant_filename(metadata_entry["id"])
        for metadata_entry in synchronized_metadata
    }
    removed_ribbon_files = remove_stale_variant_files(
        ribbon_variant_folder, expected_variant_filenames
    )
    removed_gallery_files = remove_stale_variant_files(
        gallery_variant_folder, expected_variant_filenames
    )

    for metadata_entry in synchronized_metadata:
        source_image_path = image_folder / metadata_entry["filename"]
        variant_filename = get_previous_year_variant_filename(metadata_entry["id"])
        create_webp_variant(
            source_image_path,
            ribbon_variant_folder / variant_filename,
            RIBBON_VARIANT_SIZE,
            RIBBON_VARIANT_QUALITY,
        )
        create_webp_variant(
            source_image_path,
            gallery_variant_folder / variant_filename,
            GALLERY_VARIANT_SIZE,
            GALLERY_VARIANT_QUALITY,
        )

    print(
        "Synchronized previous-years image assets:",
        f"{len(synchronized_metadata)} metadata entries,",
        f"{len(expected_variant_filenames)} ribbon variants,",
        f"{len(expected_variant_filenames)} gallery variants.",
    )
    if removed_ribbon_files or removed_gallery_files:
        print(
            "Removed stale generated files:",
            len(removed_ribbon_files) + len(removed_gallery_files),
        )


if __name__ == "__main__":
    main()
