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
class GroupedBookingOverviewRow:
    """One row in the public participant overview."""

    name: str
    canoe_count: int


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

    @property
    def all_canoes_picked_up(self) -> bool:
        """Return whether every canoe in the row has been checked off."""

        return self.total_canoes > 0 and self.picked_up_count == self.total_canoes


@dataclass
class ChecklistRowState:
    """Mutable row state used while grouping checklist rows."""

    name: str
    total_canoes: int = 0
    picked_up_count: int = 0
    canoe_entries: list[ChecklistCanoeEntry] | None = None

    def __post_init__(self) -> None:
        """Ensure each state object owns its own checklist-entry list."""

        if self.canoe_entries is None:
            self.canoe_entries = []


def build_grouped_booking_overview_rows(
    bookings: Iterable[BookedCanoe],
) -> list[GroupedBookingOverviewRow]:
    """Group confirmed canoe rows by participant name for the public overview."""

    grouped_counts: dict[str, GroupedBookingOverviewRow] = {}

    for booking in bookings:
        existing_row = grouped_counts.get(booking.name)
        if existing_row is None:
            grouped_counts[booking.name] = GroupedBookingOverviewRow(
                name=booking.name,
                canoe_count=1,
            )
            continue

        grouped_counts[booking.name] = GroupedBookingOverviewRow(
            name=existing_row.name,
            canoe_count=existing_row.canoe_count + 1,
        )

    return list(grouped_counts.values())


def build_admin_checklist_rows(bookings: Iterable[BookedCanoe]) -> list[ChecklistRow]:
    """Group booked canoes into rows suitable for the admin checklist panel."""

    grouped_rows: dict[str, ChecklistRowState] = {}

    for booking in bookings:
        row_state = grouped_rows.setdefault(
            booking.name,
            ChecklistRowState(name=booking.name),
        )
        row_state.total_canoes += 1
        if booking.picked_up:
            row_state.picked_up_count += 1

        assert row_state.canoe_entries is not None
        row_state.canoe_entries.append(
            ChecklistCanoeEntry(id=booking.id, picked_up=bool(booking.picked_up))
        )

    checklist_rows: list[ChecklistRow] = []
    for row_state in grouped_rows.values():
        assert row_state.canoe_entries is not None
        sorted_entries = tuple(
            sorted(
                row_state.canoe_entries,
                key=lambda canoe_entry: (not canoe_entry.picked_up, canoe_entry.id),
            )
        )
        checklist_rows.append(
            ChecklistRow(
                name=row_state.name,
                total_canoes=row_state.total_canoes,
                picked_up_count=row_state.picked_up_count,
                canoe_entries=sorted_entries,
            )
        )

    return checklist_rows
