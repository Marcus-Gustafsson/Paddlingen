"""Model-level tests for beginner-friendly computed helpers."""

from app.util.db_models import BookedCanoe


def test_booked_canoe_helper_properties_show_placeholders_for_missing_riders() -> None:
    """Keep the canoe display helpers predictable when riders are still unknown."""

    booked_canoe = BookedCanoe(
        participant_first_name="Marcus",
        participant_last_name="Gustafsson",
    )

    assert booked_canoe.pickup_person_name == "Marcus Gustafsson"
    assert booked_canoe.passenger_two_name_or_placeholder == "?"
    assert booked_canoe.passenger_three_name_or_placeholder == "?"
    assert booked_canoe.display_rider_names == "Marcus Gustafsson & ?"
    assert booked_canoe.has_third_rider is False
    assert booked_canoe.name == "Marcus Gustafsson"


def test_booked_canoe_helper_properties_include_named_optional_riders() -> None:
    """Return one combined rider string when optional rider names are filled in."""

    booked_canoe = BookedCanoe(
        participant_first_name="Marcus",
        participant_last_name="Gustafsson",
        passenger_two_first_name="Mathias",
        passenger_two_last_name="Axelsson",
        passenger_three_first_name="Tom",
        passenger_three_last_name="Lundberg",
    )

    assert booked_canoe.passenger_two_name_or_placeholder == "Mathias Axelsson"
    assert booked_canoe.passenger_three_name_or_placeholder == "Tom Lundberg"
    assert (
        booked_canoe.display_rider_names
        == "Marcus Gustafsson & Mathias Axelsson & Tom Lundberg"
    )
    assert booked_canoe.has_third_rider is True
