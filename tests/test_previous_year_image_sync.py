"""Tests for the previous-years image sync script helpers."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType


def load_sync_script_module() -> ModuleType:
    """Load the sync script by file path so tests do not affect mypy module discovery."""

    script_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "sync_previous_year_image_metadata.py"
    )
    script_spec = spec_from_file_location(
        "sync_previous_year_image_metadata_for_test",
        script_path,
    )
    if script_spec is None or script_spec.loader is None:
        raise AssertionError("Could not load the sync script module for testing.")

    sync_script_module = module_from_spec(script_spec)
    script_spec.loader.exec_module(sync_script_module)
    return sync_script_module


def test_remove_deleted_source_variant_files_removes_both_variant_directories(tmp_path):
    """Delete stale ribbon and gallery files when a source image disappears."""

    sync_script_module = load_sync_script_module()
    ribbon_variant_folder = tmp_path / "ribbon"
    gallery_variant_folder = tmp_path / "gallery"
    ribbon_variant_folder.mkdir()
    gallery_variant_folder.mkdir()

    kept_variant_filename = "IMG-0001.webp"
    deleted_variant_filename = "IMG-0002.webp"

    for variant_folder in (ribbon_variant_folder, gallery_variant_folder):
        (variant_folder / kept_variant_filename).write_bytes(b"keep")
        (variant_folder / deleted_variant_filename).write_bytes(b"delete")

    removed_files = sync_script_module.remove_deleted_source_variant_files(
        [{"id": "IMG-0002", "filename": "removed-source.jpg"}],
        ribbon_variant_folder=ribbon_variant_folder,
        gallery_variant_folder=gallery_variant_folder,
    )

    assert sorted(path.name for path in removed_files) == [
        deleted_variant_filename,
        deleted_variant_filename,
    ]
    assert (ribbon_variant_folder / kept_variant_filename).exists()
    assert (gallery_variant_folder / kept_variant_filename).exists()
    assert not (ribbon_variant_folder / deleted_variant_filename).exists()
    assert not (gallery_variant_folder / deleted_variant_filename).exists()
