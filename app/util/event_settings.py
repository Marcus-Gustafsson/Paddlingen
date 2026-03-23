"""Helpers for reading and seeding event settings.

This module keeps event-setting logic out of the route handlers so the public
pages, CLI commands, and tests can all use the same behavior.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from datetime import date, datetime
from typing import Any, Mapping

from flask import current_app

from .db_models import BookingOrder, Event, db


def format_swedish_date_display(event_date: date, include_year: bool = False) -> str:
    """Return a simple Swedish date string for a Python ``date`` value.

    Args:
        event_date: The date to format.
        include_year: Whether to append the year in the returned string.

    Returns:
        str: A string such as ``"20 mars"`` or ``"20 mars 2026"``.
    """

    month_names = {
        1: "januari",
        2: "februari",
        3: "mars",
        4: "april",
        5: "maj",
        6: "juni",
        7: "juli",
        8: "augusti",
        9: "september",
        10: "oktober",
        11: "november",
        12: "december",
    }
    base_display = f"{event_date.day} {month_names[event_date.month]}"
    if include_year:
        return f"{base_display} {event_date.year}"
    return base_display


EVENT_TEMPLATE_FIELD_NAMES = (
    "title",
    "subtitle",
    "start_time",
    "starting_location_name",
    "starting_location_url",
    "end_location_name",
    "end_location_url",
    "available_canoes",
    "price_per_canoe_sek",
    "max_canoes_per_booking",
    "weather_forecast_days_before_event",
    "weather_latitude",
    "weather_longitude",
    "faq_booking_text",
    "faq_changes_and_questions_text",
    "rules_on_the_water_text",
    "rules_after_paddling_text",
    "contact_email",
    "contact_phone",
)


def build_config_event_template_values(configuration: Any) -> dict[str, Any]:
    """Build the code-defined event template values from ``config.py``.

    Args:
        configuration: Flask configuration mapping, usually
            ``current_app.config``.

    Returns:
        dict[str, Any]: Default event-template values used both as fallback
        event data and as the starting point when creating the first event
        from the admin dashboard.
    """

    event_date = datetime.strptime(configuration["EVENT_DATE_ISO"], "%Y-%m-%d").date()
    start_time = datetime.strptime(configuration["EVENT_TIME_24H"], "%H:%M").time()
    event_year = event_date.year

    return {
        "title": configuration.get("EVENT_TITLE", f"Paddlingen {event_year}"),
        "subtitle": configuration["EVENT_SUBTITLE"],
        "event_date": event_date,
        "start_time": start_time,
        "starting_location_name": configuration["EVENT_STARTING_LOCATION_NAME"],
        "starting_location_url": configuration["EVENT_STARTING_LOCATION_URL"],
        "end_location_name": configuration["EVENT_END_LOCATION_NAME"],
        "end_location_url": configuration["EVENT_END_LOCATION_URL"],
        "available_canoes": configuration["AVAILABLE_CANOES"],
        "price_per_canoe_sek": normalize_money_decimal(
            configuration["CANOE_PRICE_SEK"]
        ),
        "max_canoes_per_booking": configuration["MAX_CANOES_PER_BOOKING"],
        "weather_forecast_days_before_event": configuration[
            "WEATHER_FORECAST_DAYS_BEFORE_EVENT"
        ],
        "weather_latitude": configuration["EVENT_LATITUDE"],
        "weather_longitude": configuration["EVENT_LONGITUDE"],
        "faq_booking_text": configuration["FAQ_BOOKING_TEXT"],
        "faq_changes_and_questions_text": configuration[
            "FAQ_CHANGES_AND_QUESTIONS_TEXT"
        ],
        "rules_on_the_water_text": configuration["RULES_ON_THE_WATER_TEXT"],
        "rules_after_paddling_text": configuration["RULES_AFTER_PADDLING_TEXT"],
        "contact_email": configuration["CONTACT_EMAIL"],
        "contact_phone": configuration.get("CONTACT_PHONE"),
    }


def build_event_template_values(source_event: Event | None) -> dict[str, Any]:
    """Return event-template values from a source event or config defaults.

    Args:
        source_event: Existing event row used as the template. If ``None``,
            the code-defined template values from ``config.py`` are used.

    Returns:
        dict[str, Any]: Event values that can be copied into a new event row.
    """

    if source_event is None:
        return build_config_event_template_values(current_app.config)

    return {
        field_name: getattr(source_event, field_name)
        for field_name in EVENT_TEMPLATE_FIELD_NAMES
    }


def apply_event_template_values(
    event: Event, template_values: Mapping[str, Any]
) -> None:
    """Copy shared template fields into an ``Event`` model instance.

    Args:
        event: Event row to update in memory.
        template_values: Template values returned by one of the helper
            functions in this module.
    """

    for field_name in EVENT_TEMPLATE_FIELD_NAMES:
        setattr(event, field_name, template_values[field_name])


def split_info_text_into_items(info_text: str) -> list[str]:
    """Split multi-line admin text into bullet-style list items.

    Args:
        info_text: Multi-line text where each non-empty line becomes one item.

    Returns:
        list[str]: Cleaned lines suitable for rendering in a template.
    """

    return [line.strip() for line in info_text.splitlines() if line.strip()]


def normalize_money_decimal(value: Any) -> Decimal:
    """Return a fixed-point money value rounded to two decimals."""

    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def serialize_money_value(value: Any) -> int | float:
    """Return a template- and JSON-friendly money value."""

    normalized_value = normalize_money_decimal(value)
    if normalized_value == normalized_value.to_integral_value():
        return int(normalized_value)
    return float(normalized_value)


def get_active_event() -> Event | None:
    """Return the currently active event row if one exists.

    Returns:
        Event | None: The active event row. If multiple rows are active, the
        newest one is used and a warning is logged.
    """

    active_events = (
        Event.query.filter_by(is_active=True).order_by(Event.id.desc()).all()
    )
    if not active_events:
        return None

    if len(active_events) > 1:
        current_app.logger.warning(
            "Multiple active events were found in the database. Using event id=%s.",
            active_events[0].id,
        )

    return active_events[0]


def build_event_settings_with_fallback() -> dict[str, Any]:
    """Return the event settings used by the homepage and frontend scripts.

    Database values are preferred. Missing values fall back to ``config.py``
    and generate warnings in the application log so the issue is visible
    without breaking the public page.

    Returns:
        dict[str, Any]: Event settings formatted for the existing templates and
        JavaScript modules.
    """

    configuration = current_app.config
    fallback_values = build_config_event_template_values(configuration)
    active_event = get_active_event()
    fallback_warnings: list[str] = []

    if active_event is None:
        warning_message = (
            "No active event was found in the database. Using config.py event"
            " fallback values."
        )
        current_app.logger.warning(warning_message)
        fallback_warnings.append(warning_message)

    fields_that_allow_blank_values = {"subtitle"}

    def choose_value(field_name: str) -> Any:
        fallback_value = fallback_values[field_name]
        if active_event is None:
            return fallback_value

        database_value = getattr(active_event, field_name)
        if database_value is None or (
            database_value == "" and field_name not in fields_that_allow_blank_values
        ):
            warning_message = (
                f"Active event field '{field_name}' is missing. Using config.py "
                "fallback value instead."
            )
            current_app.logger.warning(warning_message)
            fallback_warnings.append(warning_message)
            return fallback_value

        return database_value

    event_title = choose_value("title")
    event_subtitle = choose_value("subtitle")
    event_date = choose_value("event_date")
    start_time = choose_value("start_time")
    starting_location_name = choose_value("starting_location_name")
    starting_location_url = choose_value("starting_location_url")
    end_location_name = choose_value("end_location_name")
    end_location_url = choose_value("end_location_url")
    available_canoes = choose_value("available_canoes")
    price_per_canoe_sek = serialize_money_value(choose_value("price_per_canoe_sek"))
    max_canoes_per_booking = choose_value("max_canoes_per_booking")
    weather_forecast_days_before_event = choose_value(
        "weather_forecast_days_before_event"
    )
    weather_latitude = choose_value("weather_latitude")
    weather_longitude = choose_value("weather_longitude")
    faq_booking_text = choose_value("faq_booking_text")
    faq_changes_and_questions_text = choose_value("faq_changes_and_questions_text")
    rules_on_the_water_text = choose_value("rules_on_the_water_text")
    rules_after_paddling_text = choose_value("rules_after_paddling_text")
    contact_email = choose_value("contact_email")
    contact_phone = choose_value("contact_phone")

    datetime_local_iso = datetime.combine(event_date, start_time).strftime(
        "%Y-%m-%dT%H:%M:%S"
    )

    return {
        "event_id": active_event.id if active_event is not None else None,
        "source": "database" if active_event is not None else "config_fallback",
        "fallback_warnings": fallback_warnings,
        "year": event_date.year,
        "title": event_title,
        "subtitle": event_subtitle,
        "section_id": f"year-{event_date.year}",
        "event_date_iso": event_date.isoformat(),
        "date_display": format_swedish_date_display(event_date),
        "full_date_display": format_swedish_date_display(event_date, include_year=True),
        "time_display": f"Kl {start_time.strftime('%H:%M')}",
        "datetime_local_iso": datetime_local_iso,
        "location_name": starting_location_name,
        "location_url": starting_location_url,
        "starting_location_name": starting_location_name,
        "starting_location_url": starting_location_url,
        "end_location_name": end_location_name,
        "end_location_url": end_location_url,
        "available_canoes_total": available_canoes,
        "max_canoes_per_booking": max_canoes_per_booking,
        "price_per_canoe_sek": price_per_canoe_sek,
        "weather_forecast_days_before_event": weather_forecast_days_before_event,
        "weather_latitude": weather_latitude,
        "weather_longitude": weather_longitude,
        "faq_booking_items": split_info_text_into_items(faq_booking_text),
        "faq_changes_and_questions_items": split_info_text_into_items(
            faq_changes_and_questions_text
        ),
        "rules_on_the_water_items": split_info_text_into_items(rules_on_the_water_text),
        "rules_after_paddling_items": split_info_text_into_items(
            rules_after_paddling_text
        ),
        "contact_email": contact_email,
        "contact_phone": contact_phone or "",
    }


def get_available_canoes_total_with_fallback() -> int:
    """Return the current event canoe capacity with a config fallback."""

    active_event = get_active_event()
    if active_event is not None and active_event.available_canoes is not None:
        return active_event.available_canoes

    if active_event is None:
        current_app.logger.warning(
            "No active event was found when reading available canoes. "
            "Using config.py fallback value instead."
        )
    else:
        current_app.logger.warning(
            "Active event is missing 'available_canoes'. Using config.py "
            "fallback value instead."
        )

    return int(current_app.config["AVAILABLE_CANOES"])


def get_price_per_canoe_with_fallback() -> Decimal:
    """Return the current event price per canoe with a config fallback."""

    active_event = get_active_event()
    if active_event is not None and active_event.price_per_canoe_sek is not None:
        return normalize_money_decimal(active_event.price_per_canoe_sek)

    if active_event is None:
        current_app.logger.warning(
            "No active event was found when reading the canoe price. "
            "Using config.py fallback value instead."
        )
    else:
        current_app.logger.warning(
            "Active event is missing 'price_per_canoe_sek'. Using config.py "
            "fallback value instead."
        )

    return normalize_money_decimal(current_app.config["CANOE_PRICE_SEK"])


def get_max_canoes_per_booking_with_fallback() -> int:
    """Return the current event max-canoes-per-booking value with fallback."""

    active_event = get_active_event()
    if active_event is not None and active_event.max_canoes_per_booking is not None:
        return active_event.max_canoes_per_booking

    if active_event is None:
        current_app.logger.warning(
            "No active event was found when reading the booking limit. "
            "Using config.py fallback value instead."
        )
    else:
        current_app.logger.warning(
            "Active event is missing 'max_canoes_per_booking'. Using config.py "
            "fallback value instead."
        )

    return int(current_app.config["MAX_CANOES_PER_BOOKING"])


def get_weather_coordinates_with_fallback() -> tuple[float, float]:
    """Return weather coordinates for the active event with config fallbacks."""

    active_event = get_active_event()
    if (
        active_event is not None
        and active_event.weather_latitude is not None
        and active_event.weather_longitude is not None
    ):
        return float(active_event.weather_latitude), float(
            active_event.weather_longitude
        )

    if active_event is None:
        current_app.logger.warning(
            "No active event was found when reading weather coordinates. "
            "Using config.py fallback values instead."
        )
    else:
        current_app.logger.warning(
            "Active event is missing weather coordinates. Using config.py "
            "fallback values instead."
        )

    return float(current_app.config["EVENT_LATITUDE"]), float(
        current_app.config["EVENT_LONGITUDE"]
    )


def get_event_year_with_fallback() -> int:
    """Return the active event year with a config fallback."""

    active_event = get_active_event()
    if active_event is not None and active_event.event_date is not None:
        return active_event.event_date.year

    if active_event is None:
        current_app.logger.warning(
            "No active event was found when reading the event year. "
            "Using config.py fallback value instead."
        )
    else:
        current_app.logger.warning(
            "Active event is missing 'event_date'. Using config.py fallback value instead."
        )

    return (
        datetime.strptime(current_app.config["EVENT_DATE_ISO"], "%Y-%m-%d").date().year
    )


def create_or_update_active_event_from_config() -> tuple[Event, int]:
    """Create or refresh the active event row from ``config.py`` defaults.

    This command-style helper gives development and migrations a predictable
    way to create the first event row. It also backfills existing booking
    orders whose ``event_id`` is still empty.

    Returns:
        tuple[Event, int]: The active event row and the number of booking
        orders that were backfilled with its ID.
    """

    configuration = current_app.config
    fallback_values = build_config_event_template_values(configuration)
    event_date = fallback_values["event_date"]

    active_event = Event.query.filter_by(event_date=event_date).first()
    if active_event is None:
        active_event = Event(event_date=event_date)
        db.session.add(active_event)

    active_event.event_date = event_date
    apply_event_template_values(active_event, fallback_values)
    active_event.is_active = True

    db.session.flush()

    for existing_event in Event.query.filter(Event.id != active_event.id).all():
        existing_event.is_active = False

    missing_event_bookings = BookingOrder.query.filter(
        BookingOrder.event_id.is_(None)
    ).all()
    for booking_order in missing_event_bookings:
        booking_order.event_id = active_event.id

    return active_event, len(missing_event_bookings)
