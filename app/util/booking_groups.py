"""Helpers for grouped booking views in public and admin templates.

These helpers keep grouping logic out of the route handlers so both the public
participant overview and the admin event-day checklist can present booking
rows in a clearer way.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .db_models import BookedCanoe


@dataclass(frozen=True)
class GroupedCanoeDetail:
    """One canoe detail row that can later be shown under a grouped summary.

    This is the hidden detail data that later UI steps can reveal when a user
    expands one grouped pickup-person row.
    """

    booked_canoe_id: int
    canoe_label: str
    pickup_person_name: str
    second_rider_name_or_placeholder: str
    third_rider_name_or_placeholder: str
    display_rider_names: str
    has_third_rider: bool
    picked_up: bool


@dataclass(frozen=True)
class GroupedBookingOverviewRow:
    """One grouped row in the public participant overview."""

    name: str
    canoe_count: int
    canoe_details: tuple[GroupedCanoeDetail, ...]

    @property
    def pickup_person_name(self) -> str:
        """Return the group's pickup-person name with a clearer label."""

        return self.name


@dataclass(frozen=True)
class ChecklistCanoeEntry:
    """One checkbox entry in the admin event-day checklist."""

    id: int
    picked_up: bool


@dataclass(frozen=True)
class ChecklistRow:
    """One grouped checklist row for the admin event-day tool."""

    name: str
    total_canoes: int
    picked_up_count: int
    canoe_entries: tuple[ChecklistCanoeEntry, ...]
    canoe_details: tuple[GroupedCanoeDetail, ...]

    @property
    def pickup_person_name(self) -> str:
        """Return the group's pickup-person name with a clearer label."""

        return self.name

    @property
    def all_canoes_picked_up(self) -> bool:
        """Return whether every canoe in the row has been checked off."""

        return self.total_canoes > 0 and self.picked_up_count == self.total_canoes


@dataclass
class GroupedRowState:
    """Mutable row state used while grouping overview and checklist rows."""

    name: str
    bookings: list[BookedCanoe] | None = None

    def __post_init__(self) -> None:
        """Ensure each grouped row state owns its own booking list."""

        if self.bookings is None:
            self.bookings = []


def build_grouped_canoe_details(
    grouped_bookings: Iterable[BookedCanoe],
) -> tuple[GroupedCanoeDetail, ...]:
    """Return canoe-level detail rows for one grouped pickup-person row.

    Args:
        grouped_bookings: All booked canoe rows that belong to one grouped
            pickup person.

    Returns:
        tuple[GroupedCanoeDetail, ...]: Read-only canoe detail rows sorted by
        the underlying canoe row ID so later UI code gets a stable order.
    """

    sorted_grouped_bookings = sorted(grouped_bookings, key=lambda booking: booking.id)

    canoe_details: list[GroupedCanoeDetail] = []
    for canoe_number, booking in enumerate(sorted_grouped_bookings, start=1):
        canoe_details.append(
            GroupedCanoeDetail(
                booked_canoe_id=booking.id,
                canoe_label=f"Kanot {canoe_number}",
                pickup_person_name=booking.pickup_person_name,
                second_rider_name_or_placeholder=(
                    booking.passenger_two_name_or_placeholder
                ),
                third_rider_name_or_placeholder=(
                    booking.passenger_three_name_or_placeholder
                ),
                display_rider_names=booking.display_rider_names,
                has_third_rider=booking.has_third_rider,
                picked_up=bool(booking.picked_up),
            )
        )

    return tuple(canoe_details)


def group_bookings_by_pickup_person(
    bookings: Iterable[BookedCanoe],
) -> list[GroupedRowState]:
    """Group canoe rows by pickup person while preserving first-seen order."""

    grouped_rows: dict[str, GroupedRowState] = {}

    for booking in bookings:
        row_state = grouped_rows.setdefault(
            booking.pickup_person_name,
            GroupedRowState(name=booking.pickup_person_name),
        )
        assert row_state.bookings is not None
        row_state.bookings.append(booking)

    return list(grouped_rows.values())


def build_grouped_booking_overview_rows(
    bookings: Iterable[BookedCanoe],
) -> list[GroupedBookingOverviewRow]:
    """Group confirmed canoe rows by pickup person for the public overview."""

    overview_rows: list[GroupedBookingOverviewRow] = []

    for row_state in group_bookings_by_pickup_person(bookings):
        assert row_state.bookings is not None
        overview_rows.append(
            GroupedBookingOverviewRow(
                name=row_state.name,
                canoe_count=len(row_state.bookings),
                canoe_details=build_grouped_canoe_details(row_state.bookings),
            )
        )

    return overview_rows


def build_admin_checklist_rows(bookings: Iterable[BookedCanoe]) -> list[ChecklistRow]:
    """Group booked canoes into rows suitable for the admin checklist panel."""

    checklist_rows: list[ChecklistRow] = []

    for row_state in group_bookings_by_pickup_person(bookings):
        assert row_state.bookings is not None
        sorted_bookings = sorted(row_state.bookings, key=lambda booking: booking.id)
        picked_up_count = sum(1 for booking in sorted_bookings if booking.picked_up)
        sorted_entries = tuple(
            sorted(
                (
                    ChecklistCanoeEntry(
                        id=booking.id,
                        picked_up=bool(booking.picked_up),
                    )
                    for booking in sorted_bookings
                ),
                key=lambda canoe_entry: (not canoe_entry.picked_up, canoe_entry.id),
            )
        )
        checklist_rows.append(
            ChecklistRow(
                name=row_state.name,
                total_canoes=len(sorted_bookings),
                picked_up_count=picked_up_count,
                canoe_entries=sorted_entries,
                canoe_details=build_grouped_canoe_details(sorted_bookings),
            )
        )

    return checklist_rows
