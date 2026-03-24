"""Tests for grouped overview and checklist helper data."""

from app.util.booking_groups import (
    build_admin_checklist_rows,
    build_grouped_booking_overview_rows,
)
from app.util.db_models import BookedCanoe


def test_grouped_booking_overview_rows_include_canoe_detail_data() -> None:
    """Keep grouped overview rows compact while still preparing canoe details."""

    bookings = [
        BookedCanoe(
            id=14,
            participant_first_name="Marcus",
            participant_last_name="Gustafsson",
            passenger_two_first_name="Mathias",
            passenger_two_last_name="Axelsson",
        ),
        BookedCanoe(
            id=21,
            participant_first_name="Marcus",
            participant_last_name="Gustafsson",
        ),
    ]

    overview_rows = build_grouped_booking_overview_rows(bookings)

    assert len(overview_rows) == 1
    assert overview_rows[0].name == "Marcus Gustafsson"
    assert overview_rows[0].pickup_person_name == "Marcus Gustafsson"
    assert overview_rows[0].canoe_count == 2
    assert len(overview_rows[0].canoe_details) == 2
    assert overview_rows[0].canoe_details[0].canoe_label == "Kanot 1"
    assert (
        overview_rows[0].canoe_details[0].display_rider_names
        == "Marcus Gustafsson & Mathias Axelsson"
    )
    assert overview_rows[0].canoe_details[1].canoe_label == "Kanot 2"
    assert overview_rows[0].canoe_details[1].display_rider_names == (
        "Marcus Gustafsson & ?"
    )


def test_admin_checklist_rows_keep_checkbox_order_and_prepare_detail_rows() -> None:
    """Keep the current checkbox behavior while preparing later detail views."""

    bookings = [
        BookedCanoe(
            id=7,
            participant_first_name="Marcus",
            participant_last_name="Gustafsson",
            passenger_two_first_name="Mathias",
            passenger_two_last_name="Axelsson",
            picked_up=False,
        ),
        BookedCanoe(
            id=3,
            participant_first_name="Marcus",
            participant_last_name="Gustafsson",
            passenger_two_first_name="Tom",
            passenger_two_last_name="Lundberg",
            passenger_three_first_name="Mats",
            passenger_three_last_name="Nordstrom",
            picked_up=True,
        ),
    ]

    checklist_rows = build_admin_checklist_rows(bookings)

    assert len(checklist_rows) == 1
    assert checklist_rows[0].name == "Marcus Gustafsson"
    assert checklist_rows[0].total_canoes == 2
    assert checklist_rows[0].picked_up_count == 1
    assert checklist_rows[0].canoe_entries[0].id == 3
    assert checklist_rows[0].canoe_entries[0].picked_up is True
    assert checklist_rows[0].canoe_entries[1].id == 7
    assert checklist_rows[0].canoe_entries[1].picked_up is False
    assert checklist_rows[0].canoe_details[0].canoe_label == "Kanot 1"
    assert (
        checklist_rows[0].canoe_details[0].display_rider_names
        == "Marcus Gustafsson & Tom Lundberg & Mats Nordstrom"
    )
    assert checklist_rows[0].canoe_details[0].picked_up is True
    assert checklist_rows[0].canoe_details[1].canoe_label == "Kanot 2"
    assert checklist_rows[0].canoe_details[1].picked_up is False
