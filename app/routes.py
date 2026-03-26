"""Canoe Rental Booking System.

This module contains all route and view functions for the application.
Routes are attached to a :class:`~flask.Blueprint` so they can be
registered by the application factory.
"""

import logging
from collections import Counter
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from functools import wraps
import re
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo
import requests
import stripe
from flask import (
    abort,
    Blueprint,
    current_app,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from flask_login import (  # type: ignore[import-untyped]
    current_user,
    login_required,
    login_user,
    logout_user,
)
from sqlalchemy import inspect
from sqlalchemy.exc import OperationalError, ProgrammingError
from werkzeug.security import check_password_hash, generate_password_hash

from .util.event_settings import (
    apply_event_template_values,
    build_event_template_values,
    build_event_settings_with_fallback,
    format_swedish_date_display,
    get_active_event,
    get_available_canoes_total_with_fallback,
    get_event_year_with_fallback,
    get_max_canoes_per_booking_with_fallback,
    get_price_per_canoe_with_fallback,
    get_weather_coordinates_with_fallback,
    normalize_money_decimal,
)
from .util.helper_functions import (
    get_previous_year_image_metadata,
    get_previous_year_variant_folder,
    get_previous_year_variant_filename,
    get_project_root_from_static_folder,
)
from .util.checkout_preparation import (
    build_stripe_receipt_description,
    prepare_server_side_checkout_booking,
)
from .util.stripe_helpers import (
    construct_stripe_webhook_event,
    create_stripe_checkout_session,
    expire_stripe_checkout_session,
    retrieve_stripe_checkout_session,
)
from .util.stripe_webhooks import (
    confirm_paid_booking_from_checkout_session,
    process_stripe_webhook_event,
    release_expired_booking_from_checkout_session,
)
from .util.db_models import (
    BookedCanoe,
    BookingOrder,
    Event,
    PublicSiteAccessSetting,
    User,
    db,
    get_current_utc_time,
)
from .util.booking_groups import (
    build_admin_checklist_rows,
    build_grouped_booking_overview_rows,
)
from . import csrf_protect, rate_limiter

# -----------------------------------------------------------------------------
# LOGGING SETUP
# -----------------------------------------------------------------------------
# logging.basicConfig configures Python's built-in logging system so that
# log messages show up in the console. We keep INFO-level app logs in local
# development, but Stripe's SDK request logs are reduced to WARNING so normal
# homepage reads do not flood the terminal.
logging.basicConfig(level=logging.INFO)
logging.getLogger("stripe").setLevel(logging.WARNING)

# Each module should have its own logger. __name__ resolves to this file's
# import path ("main"), which helps identify where log messages originate.
logger = logging.getLogger(__name__)
MAX_PARTICIPANT_NAME_LENGTH = 20
PUBLIC_SITE_ACCESS_SESSION_KEY = "public_site_access_granted"
PUBLIC_SITE_JUST_UNLOCKED_SESSION_KEY = "public_site_just_unlocked"
PROTECTED_PREVIOUS_YEAR_STATIC_PREFIXES = (
    "/static/images/previous_years/ribbon/",
    "/static/images/previous_years/gallery/",
)
PENDING_CHECKOUT_ORDER_STATUSES = {
    "pending_payment",
    "checkout_session_created",
}
SOLD_OUT_RELOAD_MESSAGE = (
    "Tyvärr, alla kanoter hann bli reserverade innan din reservation sparades. "
    "Sidan har uppdaterats så att du ser det senaste läget."
)
STRIPE_PAYMENT_RESERVATION_EXPIRED_MESSAGE = (
    "Reservationstiden gick ut medan betalningen var öppen. "
    "Gör en ny bokning om du vill fortsätta."
)
PAYMENT_CONFIRMATION_CANCELED_HEADING = "Reservationen avbröts"
PAYMENT_CONFIRMATION_CANCELED_MESSAGE = (
    "Din reservation kunde inte slutföras automatiskt och har nu avbrutits."
)
PAYMENT_CONFIRMATION_CANCELED_NOTE = (
    "Kanoterna är inte längre reserverade för den här ordern. "
    "Gör en ny bokning från startsidan om du fortfarande vill boka en kanot."
)
PAYMENT_CONFIRMATION_PENDING_HEADING = "Betalningen väntar på bekräftelse"
PAYMENT_CONFIRMATION_PENDING_MESSAGE = (
    "Betalningen verkar redan vara registrerad hos Stripe, men bokningen är "
    "inte bekräftad lokalt ännu."
)
PAYMENT_CONFIRMATION_PENDING_NOTE = (
    "Din reservation ligger kvar medan vi väntar på den lokala bekräftelsen. "
    "Boka inte samma kanoter igen just nu."
)
PAYMENT_CONFIRMATION_UNKNOWN_NOTE = (
    "Vi kunde inte avgöra om reservationen skulle släppas. Vänta en stund "
    "och kontrollera bokningen igen om du redan har betalat."
)

main_blueprint = Blueprint("main", __name__)


def get_total_available_canoes() -> int:
    """Return the active event's total number of available canoes.

    Returns:
        int: Total number of canoes available for the active event. When the
        database has no active event row, the value falls back to ``config.py``.
    """

    return get_available_canoes_total_with_fallback()


def get_safe_login_redirect_target() -> str:
    """Return a safe post-login redirect path from the `next` query value.

    This only accepts local application paths such as `/admin` or
    `/admin?panel=events`. External absolute URLs are rejected to prevent open
    redirects.
    """

    fallback_target = url_for("main.admin_dashboard")
    next_page = request.args.get("next", "").strip()

    if not next_page:
        return fallback_target

    parsed_target = urlsplit(next_page)
    if parsed_target.scheme or parsed_target.netloc:
        logger.warning("Blocked external login redirect target: %s", next_page)
        return fallback_target

    if not parsed_target.path.startswith("/"):
        logger.warning("Blocked non-local login redirect target: %s", next_page)
        return fallback_target

    return next_page


def is_public_site_access_enabled() -> bool:
    """Return whether the shared public-site password gate is configured."""

    return bool(get_public_site_password_hash())


def get_public_site_access_setting() -> PublicSiteAccessSetting | None:
    """Return the current database-backed public access setting, if one exists."""
    try:
        return PublicSiteAccessSetting.query.order_by(
            PublicSiteAccessSetting.id.asc()
        ).first()
    except (ProgrammingError, OperationalError):
        current_app.logger.warning(
            "public_site_access_settings table is missing. "
            "Run `uv run alembic upgrade head` to add it. "
            "Falling back to PUBLIC_SITE_PASSWORD_HASH."
        )
        db.session.rollback()
        return None


def get_public_site_password_hash() -> str:
    """Return the active shared public-site password hash.

    The database-managed setting takes precedence so admins can rotate the
    password without shell access. If no database value exists yet, the app
    falls back to the existing environment-based hash.
    """

    public_access_setting = get_public_site_access_setting()
    if public_access_setting and public_access_setting.password_hash:
        return public_access_setting.password_hash

    return str(current_app.config.get("PUBLIC_SITE_PASSWORD_HASH", ""))


def ensure_public_site_access_settings_table_exists() -> None:
    """Create the password-settings table on older local databases when needed.

    The new shared-password feature was added after some development databases
    already existed. Querying can safely fall back to the environment value, but
    saving a new password needs the table to exist first.
    """

    inspector = inspect(db.engine)
    if inspector.has_table(PublicSiteAccessSetting.__tablename__):
        return

    current_app.logger.warning(
        "public_site_access_settings table is missing during password rotation. "
        "Creating it now so the admin request can complete."
    )
    PublicSiteAccessSetting.__table__.create(bind=db.engine, checkfirst=True)


def has_public_site_access() -> bool:
    """Return whether the current visitor already unlocked the public site."""

    if not is_public_site_access_enabled():
        return True

    return bool(session.get(PUBLIC_SITE_ACCESS_SESSION_KEY))


def is_protected_previous_year_static_request() -> bool:
    """Return whether the current request targets a protected static image."""

    return any(
        request.path.startswith(path_prefix)
        for path_prefix in PROTECTED_PREVIOUS_YEAR_STATIC_PREFIXES
    )


def require_public_site_access():
    """Return a redirect or JSON response when the public site is still locked."""

    if has_public_site_access():
        return None

    if request.path.startswith("/api/"):
        return jsonify({"error": "Åtkomst nekad."}), 403

    flash("Ange lösenordet för att öppna sidan.", "error")
    return redirect(url_for("main.index"))


def public_site_access_required(view_function):
    """Protect one public route behind the shared site password."""

    @wraps(view_function)
    def wrapped_view(*args, **kwargs):
        access_response = require_public_site_access()
        if access_response is not None:
            return access_response

        return view_function(*args, **kwargs)

    return wrapped_view


@main_blueprint.before_app_request
def enforce_public_site_access_gate():
    """Apply the shared public-site password gate before most routes run."""

    if has_public_site_access():
        return None

    if is_protected_previous_year_static_request():
        abort(403)

    allowed_endpoints = {
        "main.index",
        "main.stripe_webhook",
        "main.unlock_public_site",
        "main.serve_previous_year_image",
        "static",
    }
    if request.endpoint in allowed_endpoints:
        return None

    return require_public_site_access()


def get_max_canoes_per_booking() -> int:
    """Return the maximum number of canoes allowed in one booking."""

    return get_max_canoes_per_booking_with_fallback()


def get_confirmed_booked_canoes_query():
    """Return the query used for canoe rows that count as real bookings.

    The query is scoped to the active event when one exists. If the database
    has not been seeded yet, the application falls back to the older global
    query so the public page can still render.
    """

    active_event = get_active_event()
    confirmed_query = BookedCanoe.query.filter_by(status="confirmed")

    if active_event is None:
        return confirmed_query

    return confirmed_query.join(BookingOrder).filter(
        BookingOrder.event_id == active_event.id
    )


def count_confirmed_booked_canoes() -> int:
    """Return the number of confirmed canoes currently booked."""

    return get_confirmed_booked_canoes_query().count()


def count_confirmed_booked_canoes_for_event_id(event_id: int | None) -> int:
    """Return the number of confirmed canoes for one event.

    Args:
        event_id: Event primary key. When ``None``, the function falls back to
            the current active-event query.

    Returns:
        int: Number of confirmed booked canoes tied to the requested event.
    """

    if event_id is None:
        return count_confirmed_booked_canoes()

    return (
        BookedCanoe.query.filter_by(status="confirmed")
        .join(BookingOrder)
        .filter(BookingOrder.event_id == event_id)
        .count()
    )


def get_pending_checkout_orders_query(event_id: int | None = None):
    """Return pending checkout orders that can still block canoe inventory.

    Args:
        event_id: Optional event primary key used to scope the query.

    Returns:
        SQLAlchemy query for pending checkout orders.
    """

    pending_query = BookingOrder.query.filter(
        BookingOrder.status.in_(PENDING_CHECKOUT_ORDER_STATUSES)
    )

    if event_id is None:
        return pending_query.order_by(BookingOrder.id)

    return pending_query.filter(BookingOrder.event_id == event_id).order_by(
        BookingOrder.id
    )


def cleanup_expired_pending_checkout_orders(event_id: int | None = None) -> int:
    """Release expired unpaid checkout orders before counting availability.

    Args:
        event_id: Optional event primary key used to limit cleanup work.

    Returns:
        int: Number of expired orders that were released successfully.
    """

    released_order_count = 0
    for pending_order in get_pending_checkout_orders_query(event_id).all():
        if not is_booking_order_expired(pending_order):
            continue

        if cancel_pending_checkout_order(pending_order) == "released":
            released_order_count += 1

    return released_order_count


def get_active_reserved_booked_canoes_for_event_id(
    event_id: int | None,
    *,
    cleanup_expired_orders: bool = True,
) -> list[BookedCanoe]:
    """Return reserved canoe rows from still-active unpaid checkout orders.

    Args:
        event_id: Optional event primary key used to scope the count.
        cleanup_expired_orders: Whether expired pending orders should be
            released first.

    Returns:
        list[BookedCanoe]: Reserved canoe rows that still block availability.
    """

    if cleanup_expired_orders:
        cleanup_expired_pending_checkout_orders(event_id)

    reserved_canoes: list[BookedCanoe] = []
    for pending_order in get_pending_checkout_orders_query(event_id).all():
        if is_booking_order_expired(pending_order):
            continue

        reserved_canoes.extend(
            booked_canoe
            for booked_canoe in pending_order.booked_canoes
            if booked_canoe.status == "reserved"
        )

    return reserved_canoes


def count_active_reserved_canoes_for_event_id(
    event_id: int | None,
    *,
    cleanup_expired_orders: bool = True,
) -> int:
    """Return how many canoes are held by still-active unpaid reservations."""

    return len(
        get_active_reserved_booked_canoes_for_event_id(
            event_id,
            cleanup_expired_orders=cleanup_expired_orders,
        )
    )


def count_currently_unavailable_canoes_for_event_id(
    event_id: int | None,
    *,
    cleanup_expired_orders: bool = True,
) -> int:
    """Return the total canoes blocked by confirmed bookings and active holds."""

    return count_confirmed_booked_canoes_for_event_id(
        event_id
    ) + count_active_reserved_canoes_for_event_id(
        event_id,
        cleanup_expired_orders=cleanup_expired_orders,
    )


def count_currently_unavailable_canoes(
    *,
    cleanup_expired_orders: bool = True,
) -> int:
    """Return blocked canoes for the active event, including active holds.

    Args:
        cleanup_expired_orders: Whether expired pending checkout rows should be
            actively released before the count is returned.
    """

    active_event = get_active_event()
    active_event_id = active_event.id if active_event is not None else None
    return count_currently_unavailable_canoes_for_event_id(
        active_event_id,
        cleanup_expired_orders=cleanup_expired_orders,
    )


def build_public_booking_reference(booking_order_id: int) -> str:
    """Create a simple public booking reference for admins and support."""

    event_year = get_event_year_with_fallback()
    return f"PAD-{event_year}-{booking_order_id:05d}"


def format_swedish_krona_amount(amount: Decimal) -> str:
    """Return a beginner-friendly Swedish currency string for one amount."""

    normalized_amount = normalize_money_decimal(amount)
    if normalized_amount == normalized_amount.to_integral():
        integer_amount = int(normalized_amount)
        return f"{integer_amount:,}".replace(",", " ") + " kr"

    amount_text = f"{normalized_amount:,.2f}"
    amount_text = amount_text.replace(",", " ").replace(".", ",")
    return f"{amount_text} kr"


def build_booking_progress_display_data(
    booked_canoes: int,
    total_available_canoes: int,
) -> dict[str, object]:
    """Return one small payload used to render the homepage progress bar.

    The homepage should paint the current fill state immediately from the
    server-rendered booking count. A later background refresh can still fetch a
    fresh count, but the first render should not wait for JavaScript.
    """

    safe_total = max(0, total_available_canoes)
    if safe_total <= 0:
        booking_percentage = 0.0
    else:
        booking_percentage = min(100.0, max(0.0, (booked_canoes / safe_total) * 100))

    start_hue = 120.0
    end_hue = 0.0
    progress_hue = start_hue + (end_hue - start_hue) * (booking_percentage / 100)
    is_fully_booked = safe_total <= 0 or booked_canoes >= safe_total

    return {
        "width_percent": round(booking_percentage, 2),
        "bar_color": f"hsl({progress_hue:.2f}, 100%, 50%)",
        "is_fully_booked": is_fully_booked,
        "button_text": "Fullbokat" if is_fully_booked else "Boka kanot",
        "aria_disabled": "true" if is_fully_booked else "false",
    }


def is_pending_checkout_order(booking_order: BookingOrder | None) -> bool:
    """Return whether a booking is still an unpaid Stripe checkout attempt."""

    return (
        booking_order is not None
        and booking_order.status in PENDING_CHECKOUT_ORDER_STATUSES
    )


def is_booking_order_expired(booking_order: BookingOrder) -> bool:
    """Return whether the local checkout hold has already expired."""

    if booking_order.expires_at is None:
        return False

    expires_at = booking_order.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=get_current_utc_time().tzinfo)

    return expires_at <= get_current_utc_time()


def build_booking_order_expiration_iso(booking_order: BookingOrder) -> str:
    """Return the booking hold expiration time as an ISO string for the UI."""

    if booking_order.expires_at is None:
        return ""

    expires_at = booking_order.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=get_current_utc_time().tzinfo)

    return expires_at.isoformat()


def build_booked_canoe_participant_names(booked_canoe: BookedCanoe) -> list[str]:
    """Return the entered rider names for one canoe in display order.

    Args:
        booked_canoe: One booked canoe row linked to the current order.

    Returns:
        list[str]: The pickup person first, followed by any optional riders
        that were actually entered for this canoe.
    """

    participant_names = [booked_canoe.pickup_person_name]
    for first_name, last_name in (
        (
            booked_canoe.passenger_two_first_name,
            booked_canoe.passenger_two_last_name,
        ),
        (
            booked_canoe.passenger_three_first_name,
            booked_canoe.passenger_three_last_name,
        ),
    ):
        participant_name = BookedCanoe.build_full_name(first_name, last_name)
        if participant_name:
            participant_names.append(participant_name)

    return participant_names


def build_booking_order_summary_data(booking_order: BookingOrder) -> dict[str, object]:
    """Return one shared booking summary payload for UI templates."""

    canoe_summaries = [
        {
            "canoe_number": canoe_number,
            "participant_names": build_booked_canoe_participant_names(booked_canoe),
        }
        for canoe_number, booked_canoe in enumerate(
            booking_order.booked_canoes,
            start=1,
        )
    ]

    return {
        "public_booking_reference": booking_order.public_booking_reference,
        "canoe_count": booking_order.canoe_count,
        "formatted_total_amount": format_swedish_krona_amount(
            Decimal(booking_order.total_amount)
        ),
        "canoe_summaries": canoe_summaries,
    }


def build_pending_checkout_modal_data(
    booking_order: BookingOrder,
    *,
    open_on_load: bool,
) -> dict[str, object]:
    """Return the JSON-safe modal Step 3 data for one pending booking."""

    pending_checkout_data = build_booking_order_summary_data(booking_order)
    pending_checkout_data.update(
        {
            "countdown_expires_at_iso": build_booking_order_expiration_iso(
                booking_order
            ),
            "pay_now_url": url_for(
                "main.start_stripe_checkout",
                public_booking_reference=booking_order.public_booking_reference,
            ),
            "cancel_order_url": url_for(
                "main.cancel_checkout_order",
                public_booking_reference=booking_order.public_booking_reference,
            ),
            "open_on_load": open_on_load,
        }
    )
    return pending_checkout_data


def build_payment_status_api_url(
    public_booking_reference: str,
    checkout_session_id: str,
) -> str:
    """Return the polling URL used by the post-Stripe payment return page."""

    return url_for(
        "main.stripe_checkout_status",
        order_ref=public_booking_reference,
        session_id=checkout_session_id,
    )


def is_ajax_request() -> bool:
    """Return whether the current request expects a JSON-style response."""

    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def build_home_redirect_payload(message: str) -> dict[str, object]:
    """Store a home-page toast message and return redirect details for JS."""

    flash(message, "error")
    return {
        "message": message,
        "redirect_url": url_for("main.index"),
        "reload_page": True,
    }


def build_payment_return_failure_payload(
    *,
    heading: str,
    message: str,
    status_note: str,
) -> dict[str, str]:
    """Return one shared failure-card payload for the payment return page."""

    return {
        "heading": heading,
        "message": message,
        "status_note": status_note,
    }


def reconcile_pending_checkout_order_with_stripe(booking_order: BookingOrder) -> str:
    """Try to synchronize one pending booking with the latest Stripe session state.

    This is a fallback for the browser return flow when the visitor has already
    completed Stripe Checkout but the webhook has not updated the local booking
    yet. The webhook remains the normal background confirmation path.
    """

    if not is_pending_checkout_order(booking_order):
        return "not_pending"

    checkout_session_id = (booking_order.payment_provider_session_id or "").strip()
    if not checkout_session_id:
        return "missing_session"

    try:
        stripe_checkout_session = retrieve_stripe_checkout_session(checkout_session_id)
    except stripe.StripeError:
        current_app.logger.exception(
            "Stripe Checkout Session lookup failed while reconciling %s.",
            booking_order.public_booking_reference,
        )
        return "stripe_error"

    checkout_status = str(getattr(stripe_checkout_session, "status", "") or "")
    payment_status = str(getattr(stripe_checkout_session, "payment_status", "") or "")

    if payment_status == "paid":
        return confirm_paid_booking_from_checkout_session(stripe_checkout_session)

    if checkout_status == "expired":
        return release_expired_booking_from_checkout_session(stripe_checkout_session)

    return "pending"


def build_checkout_error_response(
    message: str,
    status_code: int = 400,
    *,
    reload_page: bool = False,
):
    """Return either JSON or a flash+redirect checkout error response."""

    if is_ajax_request():
        response_payload: dict[str, object] = {"ok": False, "message": message}
        if reload_page:
            response_payload.update(build_home_redirect_payload(message))
        return jsonify(response_payload), status_code

    flash(message, "error")
    return redirect(url_for("main.index"))


def cancel_pending_checkout_order(booking_order: BookingOrder) -> str:
    """Release one unpaid pending checkout order when it is still safe.

    Args:
        booking_order: Local booking order that should be released.

    Returns:
        str: Result label used by routes to decide which message to show.
        Possible values are ``released``, ``already_paid``, ``stripe_error``,
        and ``not_pending``.
    """

    if not is_pending_checkout_order(booking_order):
        return "not_pending"

    checkout_session_id = booking_order.payment_provider_session_id
    if checkout_session_id:
        try:
            stripe_checkout_session = retrieve_stripe_checkout_session(
                checkout_session_id
            )
        except stripe.StripeError:
            current_app.logger.exception(
                "Stripe Checkout Session lookup failed while cancelling %s.",
                booking_order.public_booking_reference,
            )
            return "stripe_error"

        checkout_status = str(getattr(stripe_checkout_session, "status", "") or "")
        payment_status = str(
            getattr(stripe_checkout_session, "payment_status", "") or ""
        )

        if checkout_status == "complete" or payment_status == "paid":
            return "already_paid"

        if checkout_status == "open":
            try:
                expire_stripe_checkout_session(checkout_session_id)
            except stripe.StripeError:
                current_app.logger.exception(
                    "Stripe Checkout Session expiry failed while cancelling %s.",
                    booking_order.public_booking_reference,
                )
                return "stripe_error"

    db.session.delete(booking_order)
    db.session.commit()
    return "released"


def build_canoe_rider_data_from_form(
    requested_canoes: int,
) -> list[dict[str, str | None]]:
    """Parse pickup-person and optional rider names from the booking form.

    Args:
        requested_canoes: Number of canoe rows expected from the booking form.

    Returns:
        list[dict[str, str | None]]: One dictionary per canoe containing the
        required pickup person plus optional second- and third-rider fields.
    """

    canoe_rider_rows: list[dict[str, str | None]] = []
    for canoe_number in range(1, requested_canoes + 1):
        first_name = request.form.get(f"canoe{canoe_number}_fname", "").strip()
        last_name = request.form.get(f"canoe{canoe_number}_lname", "").strip()
        passenger_two_first_name = request.form.get(
            f"canoe{canoe_number}_passenger2_fname", ""
        ).strip()
        passenger_two_last_name = request.form.get(
            f"canoe{canoe_number}_passenger2_lname", ""
        ).strip()
        passenger_three_first_name = request.form.get(
            f"canoe{canoe_number}_passenger3_fname", ""
        ).strip()
        passenger_three_last_name = request.form.get(
            f"canoe{canoe_number}_passenger3_lname", ""
        ).strip()

        if not first_name or not last_name:
            raise ValueError(
                f"Kanot {canoe_number} måste ha ett för- och efternamn för den "
                "person som hämtar ut kanoten."
            )

        if len(first_name) > MAX_PARTICIPANT_NAME_LENGTH:
            raise ValueError(
                f"Förnamnet för kanot {canoe_number} får vara högst "
                f"{MAX_PARTICIPANT_NAME_LENGTH} tecken."
            )

        if len(last_name) > MAX_PARTICIPANT_NAME_LENGTH:
            raise ValueError(
                f"Efternamnet för kanot {canoe_number} får vara högst "
                f"{MAX_PARTICIPANT_NAME_LENGTH} tecken."
            )

        if bool(passenger_two_first_name) != bool(passenger_two_last_name):
            raise ValueError(
                f"Andra personen i kanot {canoe_number} måste ha både för- och "
                "efternamn om namnet fylls i."
            )

        if bool(passenger_three_first_name) != bool(passenger_three_last_name):
            raise ValueError(
                f"Tredje personen i kanot {canoe_number} måste ha både för- och "
                "efternamn om namnet fylls i."
            )

        for optional_rider_value, optional_rider_label in (
            (
                passenger_two_first_name,
                f"Andra personens förnamn i kanot {canoe_number}",
            ),
            (
                passenger_two_last_name,
                f"Andra personens efternamn i kanot {canoe_number}",
            ),
            (
                passenger_three_first_name,
                f"Tredje personens förnamn i kanot {canoe_number}",
            ),
            (
                passenger_three_last_name,
                f"Tredje personens efternamn i kanot {canoe_number}",
            ),
        ):
            if len(optional_rider_value) > MAX_PARTICIPANT_NAME_LENGTH:
                raise ValueError(
                    f"{optional_rider_label} får vara högst "
                    f"{MAX_PARTICIPANT_NAME_LENGTH} tecken."
                )

        canoe_rider_rows.append(
            {
                "first_name": first_name,
                "last_name": last_name,
                "passenger_two_first_name": passenger_two_first_name or None,
                "passenger_two_last_name": passenger_two_last_name or None,
                "passenger_three_first_name": passenger_three_first_name or None,
                "passenger_three_last_name": passenger_three_last_name or None,
            }
        )

    return canoe_rider_rows


def normalize_participant_full_name(first_name: str, last_name: str) -> str:
    """Return a normalized full name used for booking-limit comparisons."""

    return f"{first_name.strip()} {last_name.strip()}".strip().casefold()


def validate_total_canoes_per_name(
    participant_names: list[dict[str, str | None]],
    max_canoes_per_name: int = 5,
    excluded_booking_ids: set[int] | None = None,
) -> str | None:
    """Reject bookings that would push one exact name above the total limit.

    Args:
        participant_names: Parsed participant rows from the current booking form.
        max_canoes_per_name: Maximum allowed total for one exact participant name.
        excluded_booking_ids: Optional canoe row IDs that should be ignored when
            counting existing bookings, for example while editing one existing
            admin booking row in place.

    Returns:
        str | None: Swedish validation error text when the limit would be
        exceeded, otherwise ``None``.
    """

    requested_name_counts = Counter(
        normalize_participant_full_name(
            str(participant["first_name"]), str(participant["last_name"])
        )
        for participant in participant_names
    )
    excluded_booking_ids = excluded_booking_ids or set()
    active_event = get_active_event()
    active_event_id = active_event.id if active_event is not None else None
    existing_canoe_rows = [
        *get_confirmed_booked_canoes_query().all(),
        *get_active_reserved_booked_canoes_for_event_id(active_event_id),
    ]
    existing_name_counts = Counter(
        normalize_participant_full_name(
            booking.participant_first_name,
            booking.participant_last_name,
        )
        for booking in existing_canoe_rows
        if booking.id not in excluded_booking_ids
    )

    for participant in participant_names:
        display_name = f"{participant['first_name']} {participant['last_name']}".strip()
        normalized_name = normalize_participant_full_name(
            str(participant["first_name"]),
            str(participant["last_name"]),
        )
        if (
            existing_name_counts[normalized_name]
            + requested_name_counts[normalized_name]
            > max_canoes_per_name
        ):
            return (
                f"{display_name} har redan {existing_name_counts[normalized_name]} "
                f"bokade kanoter. Samma namn kan ha högst {max_canoes_per_name} "
                "kanoter totalt."
            )

    return None


def build_event_settings() -> dict[str, object]:
    """Return the current event settings needed by templates and scripts.

    Returns:
        dict[str, object]: A beginner-friendly collection of event values used
        by the homepage template and frontend JavaScript.
    """

    return build_event_settings_with_fallback()


def escape_ical_text(value: str) -> str:
    """Return text escaped for safe use inside an iCalendar field."""

    return (
        value.replace("\\", "\\\\")
        .replace(";", r"\;")
        .replace(",", r"\,")
        .replace("\n", r"\n")
    )


def build_event_calendar_ics(event_settings: dict[str, object]) -> str:
    """Build one simple iCalendar file for the public event.

    Args:
        event_settings: Event values already prepared for the public templates.

    Returns:
        str: UTF-8 iCalendar text that calendar apps can import.
    """

    stockholm_timezone = ZoneInfo("Europe/Stockholm")
    event_start_local = datetime.fromisoformat(
        str(event_settings["datetime_local_iso"])
    ).replace(tzinfo=stockholm_timezone)
    event_start_utc = event_start_local.astimezone(ZoneInfo("UTC"))
    event_title = escape_ical_text(str(event_settings["title"]))
    event_location_name = escape_ical_text(str(event_settings["location_name"]))
    event_location_url = escape_ical_text(str(event_settings["location_url"]))
    event_date_label = escape_ical_text(str(event_settings["full_date_display"]))
    event_time_label = escape_ical_text(str(event_settings["time_display"]))
    event_contact_email = escape_ical_text(str(event_settings["contact_email"]))
    event_description = escape_ical_text(
        "Lägg till Paddlingen i din kalender. "
        f"Datum: {event_date_label}. "
        f"Tid: {event_time_label}. "
        f"Plats: {event_location_name}. "
        f"Frågor: {event_contact_email}."
    )
    current_timestamp_utc = get_current_utc_time().strftime("%Y%m%dT%H%M%SZ")
    event_timestamp_utc = event_start_utc.strftime("%Y%m%dT%H%M%SZ")
    event_uid = f"paddlingen-{event_settings['year']}-" "calendar@paddlingen.local"

    ical_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Paddlingen//Event Booking//SV",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        f"UID:{event_uid}",
        f"DTSTAMP:{current_timestamp_utc}",
        f"DTSTART:{event_timestamp_utc}",
        f"SUMMARY:{event_title}",
        f"LOCATION:{event_location_name}",
        f"DESCRIPTION:{event_description}",
        f"URL:{event_location_url}",
        "END:VEVENT",
        "END:VCALENDAR",
    ]
    return "\r\n".join(ical_lines) + "\r\n"


def build_previous_year_gallery_data() -> tuple[list[str], list[dict[str, str]]]:
    """Build ribbon and gallery image URLs for previous-year photos.

    Returns:
        tuple[list[str], list[dict[str, str]]]: Ribbon image URLs plus gallery
        image objects with stable public IDs and filenames.
    """
    image_metadata = get_previous_year_image_metadata()
    ribbon_image_urls = [
        url_for(
            "main.serve_previous_year_image",
            variant_name="ribbon",
            image_id=image_entry["id"],
        )
        for image_entry in image_metadata
    ]
    gallery_images = [
        {
            "id": image_entry["id"],
            "filename": image_entry["filename"],
            "url": url_for(
                "main.serve_previous_year_image",
                variant_name="gallery",
                image_id=image_entry["id"],
            ),
        }
        for image_entry in image_metadata
    ]
    return ribbon_image_urls, gallery_images


@main_blueprint.route("/previous-years-images/<variant_name>/<image_id>.webp")
def serve_previous_year_image(variant_name: str, image_id: str):
    """Serve one protected previous-years image variant by stable image ID.

    This route keeps the ribbon and gallery images behind the shared public
    access gate. Locked visitors should not be able to fetch the image files
    directly, even if they guess a URL.
    """

    if not has_public_site_access():
        abort(403)

    if variant_name not in {"ribbon", "gallery"}:
        abort(404)

    image_metadata = get_previous_year_image_metadata()
    known_image_ids = {image_entry["id"] for image_entry in image_metadata}
    if image_id not in known_image_ids:
        abort(404)

    static_folder = current_app.static_folder
    if static_folder is None:
        raise RuntimeError("Static folder is not configured")

    project_root = get_project_root_from_static_folder(static_folder)
    variant_folder = get_previous_year_variant_folder(project_root, variant_name)
    variant_filename = get_previous_year_variant_filename(image_id)

    if not (variant_folder / variant_filename).exists():
        abort(404)

    return send_from_directory(
        variant_folder,
        variant_filename,
        mimetype="image/webp",
    )


def get_event_coordinates() -> tuple[float, float]:
    """Return the configured latitude and longitude for the event location.

    Returns:
        tuple[float, float]: Event latitude and longitude used by the weather
        forecast integration.
    """

    return get_weather_coordinates_with_fallback()


def get_selected_admin_event(selected_event_id: int | None) -> Event | None:
    """Return the event row selected in the admin dashboard.

    Args:
        selected_event_id: Event primary key from the query string.

    Returns:
        Event | None: The requested event when it exists, otherwise the active
        event, and finally the newest event row as a safe fallback.
    """

    if selected_event_id is not None:
        selected_event = db.session.get(Event, selected_event_id)
        if selected_event is not None:
            return selected_event

    active_event = get_active_event()
    if active_event is not None:
        return active_event

    return Event.query.order_by(Event.event_date.desc()).first()


def build_admin_event_copy_defaults(source_event: Event | None) -> dict[str, str]:
    """Return starter values for the admin 'create new event' form.

    Args:
        source_event: Event used as the template for the next event.

    Returns:
        dict[str, str]: Simple string values that work directly in form inputs.
    """

    template_values = build_event_template_values(source_event)

    return {
        "new_event_date": "",
        "title": str(template_values["title"]),
        "subtitle": str(template_values["subtitle"]),
    }


def get_manual_payment_provider_from_form() -> str:
    """Return the stored payment-provider value for a manual admin booking."""

    payment_method = request.form.get("manual_payment_method", "cash").strip()
    allowed_methods = {"cash", "bank_transfer", "swish", "stripe", "other"}
    if payment_method not in allowed_methods:
        payment_method = "other"
    return f"admin_manual_{payment_method}"


def get_admin_participant_name_parts() -> tuple[str, str]:
    """Read and validate first and last name fields from the admin forms."""

    first_name = request.form.get("participant_first_name", "").strip()
    last_name = request.form.get("participant_last_name", "").strip()

    if not first_name or not last_name:
        raise ValueError("Både förnamn och efternamn måste fyllas i.")

    if len(first_name) > MAX_PARTICIPANT_NAME_LENGTH:
        raise ValueError(
            f"Förnamn får vara högst {MAX_PARTICIPANT_NAME_LENGTH} tecken långt."
        )

    if len(last_name) > MAX_PARTICIPANT_NAME_LENGTH:
        raise ValueError(
            f"Efternamn får vara högst {MAX_PARTICIPANT_NAME_LENGTH} tecken långt."
        )

    return first_name, last_name


def get_optional_admin_name_parts(
    first_name_field: str,
    last_name_field: str,
    rider_label: str,
) -> tuple[str | None, str | None]:
    """Read and validate one optional rider name pair from an admin form.

    Args:
        first_name_field: Form field name for the optional rider's first name.
        last_name_field: Form field name for the optional rider's last name.
        rider_label: Beginner-friendly Swedish label used in validation errors.

    Returns:
        tuple[str | None, str | None]: Trimmed name parts, or ``(None, None)``
        when the optional rider was left completely blank.
    """

    first_name = request.form.get(first_name_field, "").strip()
    last_name = request.form.get(last_name_field, "").strip()

    if not first_name and not last_name:
        return None, None

    if not first_name or not last_name:
        raise ValueError(f"{rider_label} måste ha både för- och efternamn.")

    if len(first_name) > MAX_PARTICIPANT_NAME_LENGTH:
        raise ValueError(
            f"{rider_label} förnamn får vara högst "
            f"{MAX_PARTICIPANT_NAME_LENGTH} tecken långt."
        )

    if len(last_name) > MAX_PARTICIPANT_NAME_LENGTH:
        raise ValueError(
            f"{rider_label} efternamn får vara högst "
            f"{MAX_PARTICIPANT_NAME_LENGTH} tecken långt."
        )

    return first_name, last_name


def get_admin_canoe_rider_data() -> dict[str, str | None]:
    """Read and validate one full canoe row from the admin booking forms."""

    first_name, last_name = get_admin_participant_name_parts()
    passenger_two_first_name, passenger_two_last_name = get_optional_admin_name_parts(
        "passenger_two_first_name",
        "passenger_two_last_name",
        "Medpaddlare 2",
    )
    (
        passenger_three_first_name,
        passenger_three_last_name,
    ) = get_optional_admin_name_parts(
        "passenger_three_first_name",
        "passenger_three_last_name",
        "Medpaddlare 3",
    )

    return {
        "first_name": first_name,
        "last_name": last_name,
        "passenger_two_first_name": passenger_two_first_name,
        "passenger_two_last_name": passenger_two_last_name,
        "passenger_three_first_name": passenger_three_first_name,
        "passenger_three_last_name": passenger_three_last_name,
    }


def parse_admin_event_form_values(event: Event) -> dict[str, object]:
    """Validate and convert the admin event form into Python values.

    Args:
        event: The existing event row being edited. Low-change values that are
            hidden in the admin form fall back to this row when they are not
            included in the submitted request.

    Returns:
        dict[str, object]: Clean values ready to assign to an :class:`Event`.

    Raises:
        ValueError: If one or more fields are missing or invalid.
    """

    title = request.form.get("title", "").strip()
    subtitle = request.form.get("subtitle", "").strip()
    starting_location_name = request.form.get("starting_location_name", "").strip()
    starting_location_url = request.form.get("starting_location_url", "").strip()
    end_location_name = request.form.get("end_location_name", "").strip()
    end_location_url = request.form.get("end_location_url", "").strip()
    contact_email = request.form.get("contact_email", "").strip()
    contact_phone = request.form.get("contact_phone", "").strip() or None
    faq_booking_text = request.form.get("faq_booking_text", "").strip()
    faq_changes_and_questions_text = request.form.get(
        "faq_changes_and_questions_text", ""
    ).strip()
    rules_on_the_water_text = request.form.get("rules_on_the_water_text", "").strip()
    rules_after_paddling_text = request.form.get(
        "rules_after_paddling_text", ""
    ).strip()

    if not all(
        [
            title,
            starting_location_name,
            starting_location_url,
            end_location_name,
            end_location_url,
            contact_email,
            faq_booking_text,
            faq_changes_and_questions_text,
            rules_on_the_water_text,
            rules_after_paddling_text,
        ]
    ):
        raise ValueError("Alla obligatoriska eventfält måste fyllas i.")

    try:
        event_date = datetime.strptime(
            request.form.get("event_date", "").strip(), "%Y-%m-%d"
        ).date()
        start_time = datetime.strptime(
            request.form.get("start_time", "").strip(), "%H:%M"
        ).time()
        available_canoes = int(request.form.get("available_canoes", "0"))
        max_canoes_per_booking = int(
            request.form.get(
                "max_canoes_per_booking", str(event.max_canoes_per_booking)
            )
        )
        weather_forecast_days_before_event = int(
            request.form.get(
                "weather_forecast_days_before_event",
                str(event.weather_forecast_days_before_event),
            )
        )
        weather_latitude = float(
            request.form.get("weather_latitude", str(event.weather_latitude))
        )
        weather_longitude = float(
            request.form.get("weather_longitude", str(event.weather_longitude))
        )
        price_per_canoe_sek = normalize_money_decimal(
            request.form.get("price_per_canoe_sek", "0")
        )
    except (TypeError, ValueError, InvalidOperation) as error:
        raise ValueError("Kunde inte läsa in eventets formulärvärden.") from error

    if available_canoes < 1:
        raise ValueError("Antal kanoter måste vara minst 1.")

    if max_canoes_per_booking < 1:
        raise ValueError("Max antal kanoter per bokning måste vara minst 1.")

    if weather_forecast_days_before_event < 0:
        raise ValueError("Väderfönstret kan inte vara negativt.")

    if price_per_canoe_sek <= Decimal("0.00"):
        raise ValueError("Pris per kanot måste vara större än 0.")

    return {
        "title": title,
        "subtitle": subtitle,
        "event_date": event_date,
        "start_time": start_time,
        "starting_location_name": starting_location_name,
        "starting_location_url": starting_location_url,
        "end_location_name": end_location_name,
        "end_location_url": end_location_url,
        "available_canoes": available_canoes,
        "price_per_canoe_sek": price_per_canoe_sek,
        "max_canoes_per_booking": max_canoes_per_booking,
        "weather_forecast_days_before_event": weather_forecast_days_before_event,
        "weather_latitude": weather_latitude,
        "weather_longitude": weather_longitude,
        "faq_booking_text": faq_booking_text,
        "faq_changes_and_questions_text": faq_changes_and_questions_text,
        "rules_on_the_water_text": rules_on_the_water_text,
        "rules_after_paddling_text": rules_after_paddling_text,
        "contact_email": contact_email,
        "contact_phone": contact_phone,
    }


@main_blueprint.route("/")
def index():
    """Homepage route handler.

    We also calculate how many canoes are still free and send that to the
    template for client-side dropdown limiting.
    """
    event_settings = build_event_settings()

    if not has_public_site_access():
        return render_template("public_lock.html", event_settings=event_settings)

    just_unlocked = bool(session.pop(PUBLIC_SITE_JUST_UNLOCKED_SESSION_KEY, False))
    pending_checkout_booking: dict[str, object] | None = None
    pending_order_id = session.get("pending_booking_order_id")
    pending_checkout_requested = request.args.get("pending_checkout") == "1"
    if pending_order_id is not None:
        pending_order = db.session.get(BookingOrder, pending_order_id)
        if is_pending_checkout_order(pending_order):
            if is_booking_order_expired(pending_order):
                cancellation_result = cancel_pending_checkout_order(pending_order)
                session.pop("pending_booking_order_id", None)
                if cancellation_result == "released":
                    flash(
                        "Reservationstiden gick ut. Gör en ny bokning om du fortfarande vill boka en kanot.",
                        "error",
                    )
                else:
                    flash(
                        "Reservationen kunde inte uppdateras automatiskt. Kontrollera bokningen igen om en stund.",
                        "error",
                    )
            else:
                pending_checkout_booking = build_pending_checkout_modal_data(
                    pending_order,
                    open_on_load=pending_checkout_requested,
                )
        elif pending_order is None:
            session.pop("pending_booking_order_id", None)

    # fetch all bookings for your overview panel
    alla_bokningar = get_confirmed_booked_canoes_query().order_by(BookedCanoe.id).all()

    total_available_canoes = int(event_settings["available_canoes_total"])

    # Read-only homepage rendering should not trigger Stripe reconciliation for
    # old pending orders. Expired holds are ignored in the count, and checkout
    # routes still perform the active cleanup when needed.
    current = count_currently_unavailable_canoes(cleanup_expired_orders=False)
    available_canoes = max(0, total_available_canoes - current)
    booking_progress = build_booking_progress_display_data(
        current,
        total_available_canoes,
    )
    (
        previous_year_ribbon_image_urls,
        previous_year_gallery_image_urls,
    ) = build_previous_year_gallery_data()
    grouped_booking_overview_rows = build_grouped_booking_overview_rows(alla_bokningar)

    return render_template(
        "index.html",
        bokningar=alla_bokningar,
        grouped_booking_overview_rows=grouped_booking_overview_rows,
        available_canoes=available_canoes,
        current_booked_canoes=current,
        booking_progress=booking_progress,
        event_settings=event_settings,
        just_unlocked=just_unlocked,
        pending_checkout_booking=pending_checkout_booking,
        previous_year_ribbon_image_urls=previous_year_ribbon_image_urls,
        previous_year_gallery_image_urls=previous_year_gallery_image_urls,
    )


@main_blueprint.route("/event.ics")
@public_site_access_required
def download_event_calendar_file():
    """Return a simple iCalendar file for the current event."""

    event_settings = build_event_settings()
    ical_response = make_response(build_event_calendar_ics(event_settings))
    ical_response.headers["Content-Type"] = "text/calendar; charset=utf-8"
    ical_response.headers["Content-Disposition"] = (
        'attachment; filename="paddlingen-event.ics"'
    )
    return ical_response


@main_blueprint.route("/unlock", methods=["POST"])
@rate_limiter.limit("5 per minute")
def unlock_public_site():
    """Unlock the public site for one browser session with the shared password."""

    if not is_public_site_access_enabled():
        return redirect(url_for("main.index"))

    submitted_password = request.form.get("password", "")
    configured_password_hash = get_public_site_password_hash()

    if not submitted_password or not configured_password_hash:
        flash("Fel lösenord. Försök igen.", "error")
        return redirect(url_for("main.index"))

    if not check_password_hash(configured_password_hash, submitted_password):
        flash("Fel lösenord. Försök igen.", "error")
        return redirect(url_for("main.index"))

    session[PUBLIC_SITE_ACCESS_SESSION_KEY] = True
    session[PUBLIC_SITE_JUST_UNLOCKED_SESSION_KEY] = True
    return redirect(url_for("main.index"))


def validate_new_password(new_password: str, confirmed_password: str) -> str | None:
    """Return a Swedish validation error message for password changes.

    Args:
        new_password: New password from the admin form.
        confirmed_password: Confirmation field from the admin form.

    Returns:
        str | None: A human-readable validation message, or ``None`` when the
        password is acceptable.
    """

    if not new_password or not confirmed_password:
        return "Båda lösenordsfälten måste fyllas i."

    if new_password != confirmed_password:
        return "Lösenorden matchar inte."

    if len(new_password) < 8:
        return "Det nya lösenordet måste vara minst 8 tecken långt."

    if len(new_password) > 255:
        return "Det nya lösenordet får vara högst 255 tecken långt."

    if not re.search(r"[A-ZÅÄÖ]", new_password):
        return "Det nya lösenordet måste innehålla minst en versal."

    if not re.search(r"\d", new_password):
        return "Det nya lösenordet måste innehålla minst en siffra."

    if not re.search(r"[^A-Za-z0-9ÅÄÖåäö]", new_password):
        return "Det nya lösenordet måste innehålla minst ett specialtecken."

    return None


@main_blueprint.route("/create-checkout-session", methods=["POST"])
@rate_limiter.limit("10 per minute")
@public_site_access_required
def payment():
    """Handle the checkout session for canoe rentals.

    1) Parse the requested canoe count.
    2) Require one active database event for real checkout preparation.
    3) Check how many are already booked.
    4) Reject requests that break booking or availability rules.
    5) Build server-approved order and Stripe-ready line-item data.
    6) Create a temporary local booking order.
    7) Create a real Stripe Checkout Session in the background.
    8) Return the pending booking data so the browser can move the modal into
       Step 3 without a full page reload.

    Storing the booking server-side means the customer cannot modify the
    canoe count, total amount, or participant names by editing browser-sent
    form fields.
    """
    # 1) get requested quantity
    try:
        requested = int(request.form["canoeCount"])
    except (ValueError, KeyError):
        return build_checkout_error_response("Ogiltigt antal kanoter.")

    active_event = get_active_event()
    if active_event is None:
        current_app.logger.warning(
            "Blocked checkout creation because no active database event exists."
        )
        return build_checkout_error_response(
            "Det finns inget aktivt event att boka just nu."
        )

    cleanup_expired_pending_checkout_orders(active_event.id)
    locked_active_event = (
        Event.query.filter_by(id=active_event.id).with_for_update().first()
    )
    if locked_active_event is None:
        return build_checkout_error_response(
            "Det gick inte att låsa eventet för bokning just nu. Försök igen om en stund.",
            status_code=503,
        )

    # 2) count confirmed bookings plus active temporary reservation holds
    current = count_currently_unavailable_canoes_for_event_id(
        locked_active_event.id,
        cleanup_expired_orders=False,
    )
    available = locked_active_event.available_canoes - current

    # 3) if they want too many, stop here
    # Log the requested and available canoe counts for debugging purposes.
    # These debug messages only appear when the logging level is set to DEBUG.
    logger.debug("User requested %d canoe(s)", requested)
    logger.debug("Canoes available before booking: %d", available)
    if requested > available:
        if available <= 0:
            return build_checkout_error_response(
                SOLD_OUT_RELOAD_MESSAGE,
                status_code=409,
                reload_page=True,
            )

        return build_checkout_error_response(
            f"Tyvärr, bara {available} kanot(er) kvar. Vänligen minska din beställning.",
            status_code=409,
        )

    if requested > locked_active_event.max_canoes_per_booking:
        return build_checkout_error_response(
            f"Du kan boka högst {locked_active_event.max_canoes_per_booking} kanoter åt gången.",
        )

    try:
        participant_names = build_canoe_rider_data_from_form(requested)
    except ValueError as error:
        return build_checkout_error_response(str(error))

    same_name_limit_error = validate_total_canoes_per_name(participant_names)
    if same_name_limit_error is not None:
        return build_checkout_error_response(same_name_limit_error)

    prepared_checkout_booking = prepare_server_side_checkout_booking(
        active_event=locked_active_event,
        canoe_count=requested,
    )

    pending_order = BookingOrder(
        event_id=prepared_checkout_booking.active_event.id,
        public_booking_reference="TEMP",
        status="pending_payment",
        canoe_count=prepared_checkout_booking.canoe_count,
        total_amount=prepared_checkout_booking.total_amount,
        currency=prepared_checkout_booking.currency,
        payment_provider="stripe_checkout",
        expires_at=get_current_utc_time() + timedelta(minutes=15),
    )
    db.session.add(pending_order)
    db.session.flush()
    pending_order.public_booking_reference = build_public_booking_reference(
        pending_order.id
    )

    for participant in participant_names:
        db.session.add(
            BookedCanoe(
                booking_order_id=pending_order.id,
                participant_first_name=participant["first_name"],
                participant_last_name=participant["last_name"],
                passenger_two_first_name=participant["passenger_two_first_name"],
                passenger_two_last_name=participant["passenger_two_last_name"],
                passenger_three_first_name=participant["passenger_three_first_name"],
                passenger_three_last_name=participant["passenger_three_last_name"],
                status="reserved",
            )
        )

    db.session.commit()

    try:
        checkout_session = create_stripe_checkout_session(
            public_booking_reference=pending_order.public_booking_reference,
            stripe_line_items=prepared_checkout_booking.stripe_line_items,
            payment_intent_description=build_stripe_receipt_description(
                active_event=prepared_checkout_booking.active_event,
                canoe_count=prepared_checkout_booking.canoe_count,
                public_booking_reference=pending_order.public_booking_reference,
            ),
            metadata={
                "booking_order_id": str(pending_order.id),
                "public_booking_reference": pending_order.public_booking_reference,
                "event_id": str(prepared_checkout_booking.active_event.id),
                "canoe_count": str(prepared_checkout_booking.canoe_count),
            },
        )
    except stripe.StripeError:
        current_app.logger.exception(
            "Stripe Checkout Session creation failed for booking reference %s.",
            pending_order.public_booking_reference,
        )
        db.session.delete(pending_order)
        db.session.commit()
        return build_checkout_error_response(
            "Det gick inte att starta betalningen just nu. Försök igen om en stund.",
            status_code=502,
        )

    pending_order.status = "checkout_session_created"
    pending_order.payment_provider = "stripe_checkout"
    pending_order.payment_provider_session_id = checkout_session.id
    db.session.commit()

    session["pending_booking_order_id"] = pending_order.id
    pending_booking_modal_data = build_pending_checkout_modal_data(
        pending_order,
        open_on_load=True,
    )
    if is_ajax_request():
        return jsonify(
            {
                "ok": True,
                "pending_booking": pending_booking_modal_data,
            }
        )

    return redirect(url_for("main.index", pending_checkout="1"))


@main_blueprint.route("/checkout/<public_booking_reference>/pay")
@public_site_access_required
def start_stripe_checkout(public_booking_reference: str):
    """Redirect the visitor from booking-modal Step 3 into Stripe."""

    pending_order = BookingOrder.query.filter_by(
        public_booking_reference=public_booking_reference
    ).first()
    if not is_pending_checkout_order(pending_order):
        flash("Ordern kunde inte hittas längre. Börja om från startsidan.", "error")
        return redirect(url_for("main.index"))

    if is_booking_order_expired(pending_order):
        cancellation_result = cancel_pending_checkout_order(pending_order)
        session.pop("pending_booking_order_id", None)
        if cancellation_result == "released":
            flash(
                "Tiden för reservationen gick ut innan betalningen startade. Gör en ny bokning om du vill fortsätta.",
                "error",
            )
        else:
            flash(
                "Betalningen kunde inte startas eftersom ordern inte längre var aktiv.",
                "error",
            )
        return redirect(url_for("main.index"))

    checkout_session_id = pending_order.payment_provider_session_id
    if not checkout_session_id:
        flash(
            "Betalningen kunde inte startas eftersom Stripe-sessionen saknas.",
            "error",
        )
        return redirect(url_for("main.index", pending_checkout="1"))

    try:
        checkout_session = retrieve_stripe_checkout_session(checkout_session_id)
    except stripe.StripeError:
        current_app.logger.exception(
            "Stripe Checkout Session lookup failed for booking reference %s.",
            pending_order.public_booking_reference,
        )
        flash(
            "Det gick inte att öppna Stripe-betalningen just nu. Försök igen om en stund.",
            "error",
        )
        return redirect(url_for("main.index", pending_checkout="1"))

    checkout_url = getattr(checkout_session, "url", None)
    if not checkout_url:
        flash(
            "Stripe skickade ingen betalningslänk för den här ordern.",
            "error",
        )
        return redirect(url_for("main.index", pending_checkout="1"))

    return redirect(str(checkout_url))


@main_blueprint.route("/checkout/<public_booking_reference>/cancel", methods=["POST"])
@public_site_access_required
def cancel_checkout_order(public_booking_reference: str):
    """Cancel one pending checkout order from booking-modal Step 3."""

    cancellation_reason = request.form.get("cancellation_reason", "manual").strip()
    pending_order = BookingOrder.query.filter_by(
        public_booking_reference=public_booking_reference
    ).first()
    cancellation_result = (
        cancel_pending_checkout_order(pending_order)
        if pending_order is not None
        else "not_pending"
    )
    session.pop("pending_booking_order_id", None)

    if cancellation_result == "released":
        if cancellation_reason == "expired":
            flash(
                "Reservationstiden gick ut. Gör en ny bokning om du fortfarande vill boka en kanot.",
                "error",
            )
        else:
            flash("Ordern avbröts. Du kan nu gå tillbaka och boka på nytt.", "error")
    elif cancellation_result == "already_paid":
        flash(
            "Ordern verkar redan vara betald hos Stripe. Kontrollera bokningsstatusen innan du försöker igen.",
            "error",
        )
    else:
        flash(
            "Ordern kunde inte avbrytas just nu. Kontrollera sidan igen om en stund.",
            "error",
        )

    return redirect(url_for("main.index"))


@main_blueprint.route("/payment-success")
@public_site_access_required
def payment_success():
    """Show the Stripe success return page after hosted Checkout finishes.

    Stripe controls when the browser leaves hosted Checkout. This route makes
    sure the visitor only sees the final local success state after the verified
    webhook has marked the booking as paid.
    """
    session.pop("pending_booking_order_id", None)

    public_booking_reference = request.args.get("order_ref", "").strip()
    checkout_session_id = request.args.get("session_id", "").strip()
    if not public_booking_reference or not checkout_session_id:
        return redirect(url_for("main.index"))

    pending_order = BookingOrder.query.filter_by(
        public_booking_reference=public_booking_reference
    ).first()
    if pending_order is None:
        flash(
            "Reservationen är inte längre aktiv. Gör en ny bokning om du vill fortsätta.",
            "error",
        )
        return redirect(url_for("main.index"))

    if pending_order.payment_provider_session_id != checkout_session_id:
        current_app.logger.warning(
            "Stripe success return session mismatch for booking reference %s.",
            public_booking_reference,
        )
        return redirect(url_for("main.index"))

    if pending_order.status != "paid" and is_booking_order_expired(pending_order):
        cancellation_result = cancel_pending_checkout_order(pending_order)
        session.pop("pending_booking_order_id", None)
        if cancellation_result == "released":
            flash(STRIPE_PAYMENT_RESERVATION_EXPIRED_MESSAGE, "error")
            return redirect(url_for("main.index"))
        if cancellation_result != "already_paid":
            flash(
                "Betalningen kunde inte kopplas till en aktiv reservation. "
                "Kontrollera startsidan igen om en stund.",
                "error",
            )
            return redirect(url_for("main.index"))

        pending_order = BookingOrder.query.filter_by(
            public_booking_reference=public_booking_reference
        ).first()
        if pending_order is None:
            flash(
                "Bokningen kunde inte hittas längre. Börja om från startsidan om du vill boka igen.",
                "error",
            )
            return redirect(url_for("main.index"))

    if pending_order.status in PENDING_CHECKOUT_ORDER_STATUSES:
        reconciliation_result = reconcile_pending_checkout_order_with_stripe(
            pending_order
        )
        if reconciliation_result == "confirmed":
            pending_order = BookingOrder.query.filter_by(
                public_booking_reference=public_booking_reference
            ).first()
        elif reconciliation_result == "released":
            flash(
                "Betalningen slutfördes inte hos Stripe och reservationen släpptes. "
                "Gör en ny bokning om du vill fortsätta.",
                "error",
            )
            return redirect(url_for("main.index"))

    if pending_order is not None and pending_order.status == "paid":
        payer_email = (pending_order.payer_email or "").strip()
        if payer_email:
            confirmation_subtitle = f"Orderbekräftelse skickas till {payer_email}"
        else:
            confirmation_subtitle = "Orderbekräftelse skickas till den e-postadress som användes i betalningen."

        return render_template(
            "payment_confirmation.html",
            page_title="Bokningen är bekräftad",
            return_heading="Din bokning är nu slutförd",
            confirmation_subtitle=confirmation_subtitle,
            booking_summary=build_booking_order_summary_data(pending_order),
            primary_link_url=url_for("main.index"),
            primary_link_label="Tillbaka till hemsidan",
        )

    return render_template(
        "payment_confirmation.html",
        page_title="Slutför din bokning",
        return_heading="Slutför din bokning",
        return_message=(
            "Vänta ett ögonblick medan bokningen slutförs. Du skickas vidare "
            "automatiskt så snart betalningen är kopplad till din bokning. "
            f"Bokningsreferens: {pending_order.public_booking_reference}."
        ),
        primary_link_url=url_for("main.index"),
        primary_link_label="Tillbaka till hemsidan",
        hide_primary_link=True,
        show_processing_indicator=True,
        payment_status_url=build_payment_status_api_url(
            pending_order.public_booking_reference,
            checkout_session_id,
        ),
        confirmed_return_url=url_for(
            "main.payment_success",
            order_ref=pending_order.public_booking_reference,
            session_id=checkout_session_id,
            confirmed="1",
        ),
        status_note=(
            "Stäng inte sidan medan bokningen slutförs. Om något går fel visas "
            "ett nytt meddelande här."
        ),
    )


@main_blueprint.route("/payment-cancel")
@public_site_access_required
def payment_cancel():
    """Release an unpaid booking after Stripe sends the visitor back."""

    public_booking_reference = request.args.get("order_ref", "").strip()
    pending_order_id = session.pop("pending_booking_order_id", None)

    pending_order = None
    if public_booking_reference:
        pending_order = BookingOrder.query.filter_by(
            public_booking_reference=public_booking_reference
        ).first()
    elif pending_order_id is not None:
        pending_order = db.session.get(BookingOrder, pending_order_id)

    if pending_order is None and public_booking_reference:
        flash(STRIPE_PAYMENT_RESERVATION_EXPIRED_MESSAGE, "error")
        return redirect(url_for("main.index"))

    reservation_was_expired = (
        pending_order is not None
        and is_pending_checkout_order(pending_order)
        and is_booking_order_expired(pending_order)
    )

    cancellation_result = (
        cancel_pending_checkout_order(pending_order)
        if pending_order is not None
        else "not_pending"
    )
    if cancellation_result == "released":
        if reservation_was_expired:
            flash(STRIPE_PAYMENT_RESERVATION_EXPIRED_MESSAGE, "error")
        else:
            flash(
                "Betalningen avbröts och reservationen släpptes. Gör en ny bokning om du vill fortsätta.",
                "error",
            )
    elif cancellation_result == "already_paid":
        flash(
            "Betalningen verkar redan vara genomförd hos Stripe. Kontrollera bokningsstatusen innan du försöker igen.",
            "error",
        )
    else:
        flash(
            "Betalningen slutfördes inte. Gör en ny bokning om du vill prova igen.",
            "error",
        )

    return redirect(url_for("main.index"))


@main_blueprint.route("/api/checkout-status")
@public_site_access_required
def stripe_checkout_status():
    """Return the local booking state for one Stripe return polling request."""

    public_booking_reference = request.args.get("order_ref", "").strip()
    checkout_session_id = request.args.get("session_id", "").strip()
    if not public_booking_reference or not checkout_session_id:
        return (
            jsonify(
                {
                    "ok": False,
                    "booking_status": "invalid_request",
                }
            ),
            400,
        )

    finalize_failed_confirmation = request.args.get("finalize_failed") == "1"

    booking_order = BookingOrder.query.filter_by(
        public_booking_reference=public_booking_reference
    ).first()
    if booking_order is None:
        response_payload = {"ok": True, "booking_status": "not_found"}
        response_payload.update(
            build_home_redirect_payload(
                "Reservationen är inte längre aktiv. Gör en ny bokning om du vill fortsätta."
            )
        )
        return jsonify(response_payload)

    if booking_order.payment_provider_session_id != checkout_session_id:
        current_app.logger.warning(
            "Blocked checkout-status lookup because the session ID did not match "
            "booking %s.",
            public_booking_reference,
        )
        response_payload = {"ok": True, "booking_status": "session_mismatch"}
        response_payload.update(
            build_payment_return_failure_payload(
                heading="Bokningen kunde inte kopplas till rätt betalning",
                message=(
                    "Betalningen kunde inte kopplas till den här bokningen automatiskt."
                ),
                status_note=(
                    "Gå tillbaka till startsidan och börja om om du fortfarande vill boka en kanot."
                ),
            )
        )
        return jsonify(response_payload)

    if booking_order.status == "paid":
        return jsonify({"ok": True, "booking_status": "paid"})

    if (
        booking_order.status in PENDING_CHECKOUT_ORDER_STATUSES
        and is_booking_order_expired(booking_order)
    ):
        cancellation_result = cancel_pending_checkout_order(booking_order)
        if cancellation_result == "released":
            response_payload = {"ok": True, "booking_status": "expired"}
            response_payload.update(
                build_home_redirect_payload(STRIPE_PAYMENT_RESERVATION_EXPIRED_MESSAGE)
            )
            return jsonify(response_payload)
        if cancellation_result == "already_paid":
            return jsonify({"ok": True, "booking_status": "pending"})
        response_payload = {"ok": True, "booking_status": "unknown"}
        response_payload.update(
            build_payment_return_failure_payload(
                heading="Bokningen kunde inte slutföras automatiskt",
                message="Bokningen kunde inte bekräftas automatiskt just nu.",
                status_note=PAYMENT_CONFIRMATION_UNKNOWN_NOTE,
            )
        )
        return jsonify(response_payload)

    if booking_order.status in PENDING_CHECKOUT_ORDER_STATUSES:
        if finalize_failed_confirmation:
            reconciliation_result = reconcile_pending_checkout_order_with_stripe(
                booking_order
            )
            if reconciliation_result == "confirmed":
                return jsonify({"ok": True, "booking_status": "paid"})
            if reconciliation_result == "released":
                response_payload = {"ok": True, "booking_status": "canceled"}
                response_payload.update(
                    build_payment_return_failure_payload(
                        heading=PAYMENT_CONFIRMATION_CANCELED_HEADING,
                        message=PAYMENT_CONFIRMATION_CANCELED_MESSAGE,
                        status_note=PAYMENT_CONFIRMATION_CANCELED_NOTE,
                    )
                )
                return jsonify(response_payload)

            cancellation_result = cancel_pending_checkout_order(booking_order)
            if cancellation_result == "released":
                response_payload = {"ok": True, "booking_status": "canceled"}
                response_payload.update(
                    build_payment_return_failure_payload(
                        heading=PAYMENT_CONFIRMATION_CANCELED_HEADING,
                        message=PAYMENT_CONFIRMATION_CANCELED_MESSAGE,
                        status_note=PAYMENT_CONFIRMATION_CANCELED_NOTE,
                    )
                )
                return jsonify(response_payload)
            if cancellation_result == "already_paid":
                reconciliation_result = reconcile_pending_checkout_order_with_stripe(
                    booking_order
                )
                if reconciliation_result == "confirmed":
                    return jsonify({"ok": True, "booking_status": "paid"})

                response_payload = {"ok": True, "booking_status": "pending"}
                response_payload.update(
                    build_payment_return_failure_payload(
                        heading=PAYMENT_CONFIRMATION_PENDING_HEADING,
                        message=PAYMENT_CONFIRMATION_PENDING_MESSAGE,
                        status_note=PAYMENT_CONFIRMATION_PENDING_NOTE,
                    )
                )
                return jsonify(response_payload)
            response_payload = {"ok": True, "booking_status": "unknown"}
            response_payload.update(
                build_payment_return_failure_payload(
                    heading="Bokningen kunde inte slutföras automatiskt",
                    message="Bokningen kunde inte bekräftas automatiskt just nu.",
                    status_note=PAYMENT_CONFIRMATION_UNKNOWN_NOTE,
                )
            )
            return jsonify(response_payload)

        return jsonify({"ok": True, "booking_status": "pending"})

    if booking_order.status in {"canceled", "payment_failed"}:
        response_payload = {"ok": True, "booking_status": booking_order.status}
        response_payload.update(
            build_payment_return_failure_payload(
                heading=PAYMENT_CONFIRMATION_CANCELED_HEADING,
                message=PAYMENT_CONFIRMATION_CANCELED_MESSAGE,
                status_note=PAYMENT_CONFIRMATION_CANCELED_NOTE,
            )
        )
        return jsonify(response_payload)

    if booking_order.status == "expired":
        response_payload = {"ok": True, "booking_status": "expired"}
        response_payload.update(
            build_payment_return_failure_payload(
                heading="Reservationstiden gick ut",
                message=STRIPE_PAYMENT_RESERVATION_EXPIRED_MESSAGE,
                status_note=PAYMENT_CONFIRMATION_CANCELED_NOTE,
            )
        )
        return jsonify(response_payload)

    response_payload = {"ok": True, "booking_status": "unknown"}
    response_payload.update(
        build_payment_return_failure_payload(
            heading="Bokningen kunde inte slutföras automatiskt",
            message="Bokningen kunde inte bekräftas automatiskt just nu.",
            status_note=PAYMENT_CONFIRMATION_UNKNOWN_NOTE,
        )
    )
    return jsonify(response_payload)


@main_blueprint.route("/stripe/webhook", methods=["POST"])
@csrf_protect.exempt
def stripe_webhook():
    """Verify and process incoming Stripe webhook events."""

    stripe_signature_header = request.headers.get("Stripe-Signature", "").strip()
    if not stripe_signature_header:
        current_app.logger.warning(
            "Rejected Stripe webhook because the Stripe-Signature header was missing."
        )
        return make_response("Missing Stripe-Signature header.", 400)

    payload = request.get_data(cache=False)

    try:
        stripe_event = construct_stripe_webhook_event(payload, stripe_signature_header)
    except ValueError:
        current_app.logger.warning(
            "Rejected Stripe webhook because the payload was invalid."
        )
        return make_response("Invalid payload.", 400)
    except stripe.SignatureVerificationError:
        current_app.logger.warning(
            "Rejected Stripe webhook because signature verification failed."
        )
        return make_response("Invalid signature.", 400)

    event_type, processing_result = process_stripe_webhook_event(stripe_event)
    current_app.logger.info(
        "Processed Stripe webhook event %s with result %s.",
        event_type,
        processing_result,
    )
    return make_response("", 200)


@main_blueprint.route("/api/booking-count")
@public_site_access_required
def get_booking_count():
    """Return the canoes currently blocking availability as JSON.

    This route counts:
        1. confirmed bookings,
        2. still-active temporary reservation holds,
        3. and excludes expired holds after cleanup.

    The JavaScript ``fetch()`` function uses this endpoint to keep the public
    progress display in sync with real availability.

    Returns:
        JSON object with the count: {"count": 25}
    """
    booking_count = count_currently_unavailable_canoes(
        cleanup_expired_orders=False,
    )
    return jsonify({"count": booking_count})


@main_blueprint.route("/login", methods=["GET", "POST"])
@rate_limiter.limit("5 per minute")  # max 5 login attempts per minute per IP
def login():
    """Display and handle the login form.

    On GET: render the form.
    On POST: validate credentials, call ``login_user()``, then redirect.
    """
    if current_user.is_authenticated:
        # Already logged in? Go to admin dashboard.
        return redirect(get_safe_login_redirect_target())

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            # Log in this user (stores user.id in session)
            login_user(user)
            return redirect(get_safe_login_redirect_target())
        else:
            flash("Felaktigt användarnamn eller lösenord", "error")

    return render_template("login.html")


@main_blueprint.route("/logout")
@login_required
def logout():
    """Logs out the current user and redirects to login."""
    logout_user()
    flash("Du har loggats ut.", "info")
    return redirect(url_for("main.login"))


# MET Norway Weather API endpoint
MET_API_URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact"

# === Simple weather code to emoji mapping ===
# You can expand or improve this later to match actual weather symbols from MET Norway
WEATHER_EMOJIS = {
    "clearsky": "☀️",
    "cloudy": "☁️",
    "fair": "🌤️",
    "fog": "🌫️",
    "heavyrain": "🌧️",
    "lightrain": "🌦️",
    "rain": "🌧️",
    "snow": "❄️",
    "heavysnow": "🌨️",
    "partlycloudy": "⛅",
    "thunderstorm": "⛈️",
}


@main_blueprint.route("/api/forecast")
@public_site_access_required
def get_forecast():
    """Fetch weather forecast for a specific date.

    Tries to get data starting at 10:00 UTC, using the next 6 hours
    forecast. If 10:00 is unavailable, uses 12:00 UTC as a fallback.
    Returns temperature, rain amount and weather icon. The request to the
    MET Norway API times out after five seconds and network failures
    produce a ``503`` JSON response.
    """
    headers = {
        "User-Agent": "PaddlingenEventApp/1.0 (contact@example.com)"  # Required by MET API
    }
    latitude, longitude = get_event_coordinates()
    params = {"lat": latitude, "lon": longitude}

    target_date = request.args.get("date")
    if not target_date:
        return (
            jsonify({"error": "Missing required 'date' parameter (YYYY-MM-DD)."}),
            400,
        )

    try:
        # A short timeout prevents the API call from hanging indefinitely
        response = requests.get(MET_API_URL, headers=headers, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        # Define desired forecast times in UTC (10:00 and fallback 12:00)
        preferred_times = ["10:00:00Z", "12:00:00Z"]

        selected_entry = None
        for time_option in preferred_times:
            target_timestamp = f"{target_date}T{time_option}"
            for entry in data["properties"]["timeseries"]:
                if entry["time"] == target_timestamp:
                    selected_entry = entry
                    break
            if selected_entry:
                break

        if not selected_entry:
            return (
                jsonify(
                    {
                        "error": "No forecast available at 10:00 or 12:00 UTC for this date."
                    }
                ),
                404,
            )

        # Extract details
        temp = selected_entry["data"]["instant"]["details"].get("air_temperature")
        rain = (
            selected_entry["data"]
            .get("next_6_hours", {})
            .get("details", {})
            .get("precipitation_amount", 0)
        )
        symbol_code = (
            selected_entry["data"]
            .get("next_6_hours", {})
            .get("summary", {})
            .get("symbol_code", "cloudy")
        )
        base_symbol = symbol_code.split("_")[0]

        forecast = {
            "temperature": round(temp) if temp is not None else "N/A",
            "rainChance": str(rain).replace(".", ","),  # simple approximation
            "icon": WEATHER_EMOJIS.get(base_symbol, "☁️"),
        }
        return jsonify(forecast)

    except requests.RequestException:
        # Return a clear message to the client on upstream failures/timeouts
        return (
            jsonify({"error": "Weather service unreachable."}),
            503,
        )


@main_blueprint.route("/admin")
@login_required
def admin_dashboard():
    """Show the admin dashboard page.

    The page is organized around two primary admin actions: booking management
    and event management. The current active event is used for the summary
    cards and for the booking list.
    """
    bookings = get_confirmed_booked_canoes_query().order_by(BookedCanoe.id).all()
    events = Event.query.order_by(Event.event_date.desc()).all()
    active_event = get_active_event()
    selected_event = get_selected_admin_event(request.args.get("event_id", type=int))
    confirmed_booking_count = len(bookings)
    available_canoes_total = get_total_available_canoes()
    public_site_access_setting = get_public_site_access_setting()
    checklist_rows = build_admin_checklist_rows(bookings) if active_event else []

    return render_template(
        "admin.html",
        bookings=bookings,
        events=events,
        active_event=active_event,
        format_swedish_date_display=format_swedish_date_display,
        selected_event=selected_event,
        confirmed_booking_count=confirmed_booking_count,
        available_canoes_total=available_canoes_total,
        checklist_rows=checklist_rows,
        create_event_defaults=build_admin_event_copy_defaults(selected_event),
        public_site_password_managed_in_database=public_site_access_setting is not None,
        public_site_password_updated_at=(
            public_site_access_setting.updated_at
            if public_site_access_setting is not None
            else None
        ),
        open_admin_panel=request.args.get("panel", ""),
    )


@main_blueprint.route("/admin/checklist", methods=["POST"])
@login_required
def admin_update_checklist():
    """Save the event-day pickup checklist for the active event."""

    active_event = get_active_event()
    if active_event is None:
        flash("Det finns inget aktivt event att checka av ännu.", "error")
        return redirect(url_for("main.admin_dashboard", panel="checklist"))

    checked_booking_ids: set[int] = set()
    for booking_id_raw in request.form.getlist("picked_up_booking_ids"):
        try:
            checked_booking_ids.add(int(booking_id_raw))
        except ValueError:
            flash("Checklistan innehöll ett ogiltigt boknings-id.", "error")
            return redirect(url_for("main.admin_dashboard", panel="checklist"))

    active_event_bookings = (
        BookedCanoe.query.filter_by(status="confirmed")
        .join(BookingOrder)
        .filter(BookingOrder.event_id == active_event.id)
        .order_by(BookedCanoe.id)
        .all()
    )

    for booked_canoe in active_event_bookings:
        booked_canoe.picked_up = booked_canoe.id in checked_booking_ids

    db.session.commit()
    flash("Checklistan uppdaterades.", "success")
    return redirect(url_for("main.admin_dashboard", panel="checklist"))


@main_blueprint.route("/admin/public-site-password", methods=["POST"])
@login_required
def admin_update_public_site_password():
    """Rotate the shared public-site password from the admin dashboard."""

    new_password = request.form.get("new_public_site_password", "")
    confirmed_password = request.form.get("confirm_public_site_password", "")

    validation_error = validate_new_password(new_password, confirmed_password)
    if validation_error is not None:
        flash(validation_error, "error")
        return redirect(url_for("main.admin_dashboard", panel="publicSitePassword"))

    try:
        ensure_public_site_access_settings_table_exists()

        public_access_setting = get_public_site_access_setting()
        if public_access_setting is None:
            public_access_setting = PublicSiteAccessSetting(
                password_hash=generate_password_hash(new_password)
            )
            db.session.add(public_access_setting)
        else:
            public_access_setting.password_hash = generate_password_hash(new_password)

        db.session.commit()
    except (ProgrammingError, OperationalError):
        db.session.rollback()
        current_app.logger.exception(
            "Failed to save the shared public-site password from the admin page."
        )
        flash(
            "Det gick inte att spara lösenordet just nu. Försök igen eller kör "
            "`uv run alembic upgrade head` om databasen är gammal.",
            "error",
        )
        return redirect(url_for("main.admin_dashboard", panel="publicSitePassword"))

    flash("Hemsidans gemensamma lösenord har uppdaterats.", "success")
    return redirect(url_for("main.admin_dashboard"))


@main_blueprint.route("/admin/account-password", methods=["POST"])
@login_required
def admin_update_account_password():
    """Allow the logged-in admin to change their own login password."""

    new_password = request.form.get("new_admin_password", "")
    confirmed_password = request.form.get("confirm_admin_password", "")

    validation_error = validate_new_password(new_password, confirmed_password)
    if validation_error is not None:
        flash(validation_error, "error")
        return redirect(url_for("main.admin_dashboard", panel="adminAccountPassword"))

    current_user.set_password(new_password)
    db.session.commit()
    flash("Ditt adminlösenord har uppdaterats.", "success")
    return redirect(url_for("main.admin_dashboard"))


@main_blueprint.route("/admin/add", methods=["POST"])
@login_required
def admin_add():
    """Handle the "Add new booking" form submission.

    • Reads one canoe's rider names from form data.
    • If non-empty, creates a one-canoe manual booking order and canoe row.
    • Redirects back to the dashboard.
    """
    try:
        canoe_rider_data = get_admin_canoe_rider_data()
    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("main.admin_dashboard", panel="bookings"))

    same_name_limit_error = validate_total_canoes_per_name([canoe_rider_data])
    if same_name_limit_error is not None:
        flash(same_name_limit_error, "error")
        return redirect(url_for("main.admin_dashboard", panel="bookings"))

    active_event = get_active_event()
    if active_event is None:
        current_app.logger.warning(
            "Admin created a manual booking without an active database event."
        )

    booking_order = BookingOrder(
        event_id=active_event.id if active_event is not None else None,
        public_booking_reference="TEMP",
        status="paid",
        canoe_count=1,
        total_amount=get_price_per_canoe_with_fallback(),
        currency="sek",
        payment_provider=get_manual_payment_provider_from_form(),
        paid_at=get_current_utc_time(),
    )
    db.session.add(booking_order)
    db.session.flush()
    booking_order.public_booking_reference = build_public_booking_reference(
        booking_order.id
    )

    booked_canoe = BookedCanoe(
        booking_order_id=booking_order.id,
        participant_first_name=str(canoe_rider_data["first_name"]),
        participant_last_name=str(canoe_rider_data["last_name"]),
        passenger_two_first_name=canoe_rider_data["passenger_two_first_name"],
        passenger_two_last_name=canoe_rider_data["passenger_two_last_name"],
        passenger_three_first_name=canoe_rider_data["passenger_three_first_name"],
        passenger_three_last_name=canoe_rider_data["passenger_three_last_name"],
        status="confirmed",
    )
    db.session.add(booked_canoe)
    db.session.commit()

    return redirect(url_for("main.admin_dashboard", panel="bookings"))


@main_blueprint.route("/admin/update/<int:id>", methods=["POST"])
@login_required
def admin_update(id):
    """Handle editing an existing canoe booking.

    • Fetches the ``BookedCanoe`` record by ``id`` or 404s.
    • Reads the updated pickup-person and optional rider values.
    • If valid, updates the record and commits.
    • Redirects back to the dashboard.
    """
    booking = db.session.get(BookedCanoe, id)
    if booking is None:
        abort(404)

    try:
        canoe_rider_data = get_admin_canoe_rider_data()
    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("main.admin_dashboard", panel="bookings"))

    same_name_limit_error = validate_total_canoes_per_name(
        [canoe_rider_data],
        excluded_booking_ids={booking.id},
    )
    if same_name_limit_error is not None:
        flash(same_name_limit_error, "error")
        return redirect(url_for("main.admin_dashboard", panel="bookings"))

    booking.participant_first_name = str(canoe_rider_data["first_name"])
    booking.participant_last_name = str(canoe_rider_data["last_name"])
    booking.passenger_two_first_name = canoe_rider_data["passenger_two_first_name"]
    booking.passenger_two_last_name = canoe_rider_data["passenger_two_last_name"]
    booking.passenger_three_first_name = canoe_rider_data["passenger_three_first_name"]
    booking.passenger_three_last_name = canoe_rider_data["passenger_three_last_name"]
    db.session.commit()
    return redirect(url_for("main.admin_dashboard", panel="bookings"))


@main_blueprint.route("/admin/delete/<int:id>", methods=["POST"])
@login_required
def admin_delete(id):
    """Handle deletion of a booking.

    • Fetches the ``BookedCanoe`` record by ``id`` or 404s.
    • Deletes it, commits the transaction.
    • Redirects back to the dashboard.
    """
    booking = db.session.get(BookedCanoe, id)
    if booking is None:
        abort(404)
    parent_order = booking.booking_order
    db.session.delete(booking)
    db.session.flush()
    if (
        parent_order
        and not BookedCanoe.query.filter_by(booking_order_id=parent_order.id).count()
    ):
        db.session.delete(parent_order)
    db.session.commit()
    return redirect(url_for("main.admin_dashboard", panel="bookings"))


@main_blueprint.route("/admin/events/create", methods=["POST"])
@login_required
def admin_create_event():
    """Create a new event from the selected event or the code template."""

    source_event = get_selected_admin_event(
        request.form.get("source_event_id", type=int)
    )
    template_values = build_event_template_values(source_event)
    if source_event is None:
        redirect_values = {"panel": "events"}
    else:
        redirect_values = {"panel": "events", "event_id": source_event.id}

    new_event_date_raw = request.form.get("new_event_date", "").strip()
    try:
        new_event_date = datetime.strptime(new_event_date_raw, "%Y-%m-%d").date()
    except ValueError:
        flash("Ange ett giltigt datum för det nya eventet.", "error")
        return redirect(url_for("main.admin_dashboard", **redirect_values))

    if Event.query.filter_by(event_date=new_event_date).first() is not None:
        flash("Det finns redan ett event med det datumet.", "error")
        return redirect(url_for("main.admin_dashboard", **redirect_values))

    created_event = Event(event_date=new_event_date, is_active=False)
    apply_event_template_values(created_event, template_values)
    created_event.title = request.form.get("new_title", "").strip() or str(
        template_values["title"]
    )
    created_event.subtitle = request.form.get("new_subtitle", "").strip() or str(
        template_values["subtitle"]
    )
    db.session.add(created_event)
    db.session.commit()

    flash("Nytt event skapades från den valda mallen.", "success")
    return redirect(
        url_for(
            "main.admin_dashboard",
            panel="events",
            event_id=created_event.id,
        )
    )


@main_blueprint.route("/admin/events/update/<int:event_id>", methods=["POST"])
@login_required
def admin_update_event(event_id: int):
    """Update one existing event from the admin dashboard form."""

    event = db.session.get(Event, event_id)
    if event is None:
        abort(404)

    try:
        cleaned_values = parse_admin_event_form_values(event)
    except ValueError as error:
        flash(str(error), "error")
        return redirect(
            url_for("main.admin_dashboard", panel="events", event_id=event.id)
        )

    event_with_same_date = Event.query.filter(
        Event.event_date == cleaned_values["event_date"],
        Event.id != event.id,
    ).first()
    if event_with_same_date is not None:
        flash("Det finns redan ett event med det datumet.", "error")
        return redirect(
            url_for("main.admin_dashboard", panel="events", event_id=event.id)
        )

    for field_name, field_value in cleaned_values.items():
        setattr(event, field_name, field_value)

    db.session.commit()
    flash("Eventet uppdaterades.", "success")
    return redirect(url_for("main.admin_dashboard", panel="events", event_id=event.id))


@main_blueprint.route("/admin/events/activate/<int:event_id>", methods=["POST"])
@login_required
def admin_activate_event(event_id: int):
    """Mark one event as the active event shown on the public site."""

    event_to_activate = db.session.get(Event, event_id)
    if event_to_activate is None:
        abort(404)

    for existing_event in Event.query.all():
        existing_event.is_active = existing_event.id == event_to_activate.id

    db.session.commit()
    flash(
        f'Eventet "{event_to_activate.event_date.strftime("%Y-%m-%d")}" är nu aktivt på hemsidan.',
        "success",
    )
    return redirect(
        url_for(
            "main.admin_dashboard",
            panel="events",
            event_id=event_to_activate.id,
        )
    )


@main_blueprint.app_errorhandler(429)
def ratelimit_handler(e):
    """Custom handler for rate limit errors (HTTP 429).

    We return a friendly JSON or HTML message.
    """
    # If the client expects JSON:
    if request.path.startswith("/api/"):
        return jsonify(error="Too many requests, please try again later."), 429
    # Otherwise render a template or plain text:
    return make_response(
        "Too many requests. Please slow down and try again in a few minutes.", 429
    )
