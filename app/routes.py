"""Canoe Rental Booking System.

This module contains all route and view functions for the application.
Routes are attached to a :class:`~flask.Blueprint` so they can be
registered by the application factory.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from functools import wraps
from urllib.parse import urlsplit
import requests
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
from werkzeug.security import check_password_hash

from .util.event_settings import (
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
from .util.db_models import (
    BookedCanoe,
    BookingOrder,
    Event,
    User,
    db,
    get_current_utc_time,
)
from . import rate_limiter

# -----------------------------------------------------------------------------
# LOGGING SETUP
# -----------------------------------------------------------------------------
# logging.basicConfig configures Python's built-in logging system so that
# log messages show up in the console. We set level=INFO to display info logs
# and above by default; debug logs require level DEBUG.
logging.basicConfig(level=logging.INFO)

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

    return bool(current_app.config.get("PUBLIC_SITE_PASSWORD_HASH"))


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


def build_public_booking_reference(booking_order_id: int) -> str:
    """Create a simple public booking reference for admins and support."""

    event_year = get_event_year_with_fallback()
    return f"PAD-{event_year}-{booking_order_id:05d}"


def build_participant_names_from_form(requested_canoes: int) -> list[dict[str, str]]:
    """Parse participant first and last names from the booking form.

    Args:
        requested_canoes: Number of canoe rows expected from the booking form.

    Returns:
        list[dict[str, str]]: One dictionary per canoe with separate first and
        last name fields.
    """

    participants: list[dict[str, str]] = []
    for canoe_number in range(1, requested_canoes + 1):
        first_name = request.form.get(f"canoe{canoe_number}_fname", "").strip()
        last_name = request.form.get(f"canoe{canoe_number}_lname", "").strip()

        if not first_name and not last_name:
            first_name = "Unnamed"
            last_name = f"participant {canoe_number}"

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

        participants.append(
            {
                "first_name": first_name,
                "last_name": last_name,
            }
        )

    return participants


def build_event_settings() -> dict[str, object]:
    """Return the current event settings needed by templates and scripts.

    Returns:
        dict[str, object]: A beginner-friendly collection of event values used
        by the homepage template and frontend JavaScript.
    """

    return build_event_settings_with_fallback()


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

    if source_event is None:
        return {
            "new_event_date": "",
            "title": "",
            "subtitle": "",
        }

    return {
        "new_event_date": "",
        "title": source_event.title,
        "subtitle": source_event.subtitle,
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

    # fetch all bookings for your overview panel
    alla_bokningar = get_confirmed_booked_canoes_query().order_by(BookedCanoe.id).all()

    # server‐side business rule from config
    current = count_confirmed_booked_canoes()
    available_canoes = max(0, get_total_available_canoes() - current)
    (
        previous_year_ribbon_image_urls,
        previous_year_gallery_image_urls,
    ) = build_previous_year_gallery_data()

    return render_template(
        "index.html",
        bokningar=alla_bokningar,
        available_canoes=available_canoes,
        event_settings=event_settings,
        just_unlocked=just_unlocked,
        previous_year_ribbon_image_urls=previous_year_ribbon_image_urls,
        previous_year_gallery_image_urls=previous_year_gallery_image_urls,
    )


@main_blueprint.route("/unlock", methods=["POST"])
@rate_limiter.limit("5 per minute")
def unlock_public_site():
    """Unlock the public site for one browser session with the shared password."""

    if not is_public_site_access_enabled():
        return redirect(url_for("main.index"))

    submitted_password = request.form.get("password", "")
    configured_password_hash = current_app.config.get("PUBLIC_SITE_PASSWORD_HASH", "")

    if not submitted_password or not configured_password_hash:
        flash("Fel lösenord. Försök igen.", "error")
        return redirect(url_for("main.index"))

    if not check_password_hash(configured_password_hash, submitted_password):
        flash("Fel lösenord. Försök igen.", "error")
        return redirect(url_for("main.index"))

    session[PUBLIC_SITE_ACCESS_SESSION_KEY] = True
    session[PUBLIC_SITE_JUST_UNLOCKED_SESSION_KEY] = True
    return redirect(url_for("main.index"))


@main_blueprint.route("/create-checkout-session", methods=["POST"])
@rate_limiter.limit("10 per minute")
@public_site_access_required
def payment():
    """Handle the checkout session for canoe rentals.

    1) Parse the requested canoe count.
    2) Check how many are already booked.
    3) If they ask for more than available → reject immediately.
    4) Otherwise create a temporary booking order and proceed to
       ``payment_success``.

    Storing the booking server-side means the customer cannot modify the
    canoe count or the participant names by editing their browser cookie.
    """
    # 1) get requested quantity
    try:
        requested = int(request.form["canoeCount"])
    except (ValueError, KeyError):
        flash("Ogiltigt antal kanoter.", "error")
        return redirect(url_for("main.index"))

    # 2) count existing confirmed bookings
    current = count_confirmed_booked_canoes()
    available = get_total_available_canoes() - current

    # 3) if they want too many, stop here
    # Log the requested and available canoe counts for debugging purposes.
    # These debug messages only appear when the logging level is set to DEBUG.
    logger.debug("User requested %d canoe(s)", requested)
    logger.debug("Canoes available before booking: %d", available)
    if requested > available:
        flash(
            f"Tyvärr, bara {available} kanot(er) kvar. Vänligen minska din beställning.",
            "error",
        )
        return redirect(url_for("main.index"))

    if requested > get_max_canoes_per_booking():
        flash(
            f"Du kan boka högst {get_max_canoes_per_booking()} kanoter åt gången.",
            "error",
        )
        return redirect(url_for("main.index"))

    try:
        participant_names = build_participant_names_from_form(requested)
    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("main.index"))
    active_event = get_active_event()
    if active_event is None:
        current_app.logger.warning(
            "Creating a booking without an active database event. "
            "Fallback config values were used for the public page."
        )

    pending_order = BookingOrder(
        event_id=active_event.id if active_event is not None else None,
        public_booking_reference="TEMP",
        status="pending_payment",
        canoe_count=requested,
        total_amount=requested * get_price_per_canoe_with_fallback(),
        currency="sek",
        payment_provider="simulated",
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
                status="reserved",
            )
        )

    db.session.commit()

    session["pending_booking_order_id"] = pending_order.id
    return redirect(url_for("main.payment_success"))


@main_blueprint.route("/payment-success")
@public_site_access_required
def payment_success():
    """Finalize the booking after (simulated) payment.

    Steps:
        1. Look up the pending booking order referenced in the user's session.
        2. Re-check availability to avoid overbooking.
        3. Mark the order and its canoe rows as confirmed.

    By storing only the database ID in the session and the actual booking
    details on the server we prevent clients from tampering with their
    reservations.
    """
    pending_order_id = session.pop("pending_booking_order_id", None)
    if not pending_order_id:
        # No reference → user reloaded or came here directly
        return redirect(url_for("main.index"))

    pending_order = db.session.get(BookingOrder, pending_order_id)
    if not pending_order:
        return redirect(url_for("main.index"))

    requested = pending_order.canoe_count
    current = count_confirmed_booked_canoes_for_event_id(pending_order.event_id)
    available_canoes_for_event = (
        pending_order.event.available_canoes
        if pending_order.event is not None
        else get_total_available_canoes()
    )
    if current + requested > available_canoes_for_event:
        flash("Ojdå! Någon hann boka före dig. Försök igen med färre kanoter.", "error")
        db.session.delete(pending_order)
        db.session.commit()
        return redirect(url_for("main.index"))

    pending_order.status = "paid"
    pending_order.paid_at = get_current_utc_time()
    for booked_canoe in pending_order.booked_canoes:
        booked_canoe.status = "confirmed"

    db.session.commit()

    return redirect(url_for("main.index"))


@main_blueprint.route("/api/booking-count")
@public_site_access_required
def get_booking_count():
    """Return the current number of bookings as JSON.

    This route:
        1. Counts confirmed bookings for the active event when one exists.
        2. Falls back to the older global count if no active event exists yet.
        3. Returns the count as JSON data.

    The JavaScript ``fetch()`` function will call this endpoint.

    Returns:
        JSON object with the count: {"count": 25}
    """
    # Count confirmed rows for the active event.
    booking_count = count_confirmed_booked_canoes()

    # Return the count as JSON
    # jsonify() converts Python data to JSON format that JavaScript can read
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
    available_canoes_total = (
        active_event.available_canoes if active_event is not None else 0
    )
    remaining_canoes = max(0, available_canoes_total - confirmed_booking_count)

    return render_template(
        "admin.html",
        bookings=bookings,
        events=events,
        active_event=active_event,
        format_swedish_date_display=format_swedish_date_display,
        selected_event=selected_event,
        confirmed_booking_count=confirmed_booking_count,
        remaining_canoes=remaining_canoes,
        create_event_defaults=build_admin_event_copy_defaults(selected_event),
        open_admin_panel=request.args.get("panel", ""),
    )


@main_blueprint.route("/admin/add", methods=["POST"])
@login_required
def admin_add():
    """Handle the "Add new booking" form submission.

    • Reads first and last name from form data.
    • If non-empty, creates a one-canoe manual booking order and canoe row.
    • Redirects back to the dashboard.
    """
    try:
        first_name, last_name = get_admin_participant_name_parts()
    except ValueError as error:
        flash(str(error), "error")
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
        participant_first_name=first_name,
        participant_last_name=last_name,
        status="confirmed",
    )
    db.session.add(booked_canoe)
    db.session.commit()

    return redirect(url_for("main.admin_dashboard", panel="bookings"))


@main_blueprint.route("/admin/update/<int:id>", methods=["POST"])
@login_required
def admin_update(id):
    """Handle editing an existing booking's name.

    • Fetches the ``BookedCanoe`` record by ``id`` or 404s.
    • Reads the new first and last name values.
    • If valid, updates the record and commits.
    • Redirects back to the dashboard.
    """
    booking = db.session.get(BookedCanoe, id)
    if booking is None:
        abort(404)

    try:
        first_name, last_name = get_admin_participant_name_parts()
    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("main.admin_dashboard", panel="bookings"))

    booking.participant_first_name = first_name
    booking.participant_last_name = last_name
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
    """Create a new event by copying the currently selected event."""

    source_event = get_selected_admin_event(
        request.form.get("source_event_id", type=int)
    )
    if source_event is None:
        flash("Det gick inte att hitta ett event att kopiera från.", "error")
        return redirect(url_for("main.admin_dashboard", panel="events"))

    new_event_date_raw = request.form.get("new_event_date", "").strip()
    try:
        new_event_date = datetime.strptime(new_event_date_raw, "%Y-%m-%d").date()
    except ValueError:
        flash("Ange ett giltigt datum för det nya eventet.", "error")
        return redirect(
            url_for(
                "main.admin_dashboard",
                panel="events",
                event_id=source_event.id,
            )
        )

    if Event.query.filter_by(event_date=new_event_date).first() is not None:
        flash("Det finns redan ett event med det datumet.", "error")
        return redirect(
            url_for(
                "main.admin_dashboard",
                panel="events",
                event_id=source_event.id,
            )
        )

    created_event = Event(
        title=request.form.get("new_title", "").strip() or source_event.title,
        subtitle=request.form.get("new_subtitle", "").strip() or source_event.subtitle,
        event_date=new_event_date,
        start_time=source_event.start_time,
        starting_location_name=source_event.starting_location_name,
        starting_location_url=source_event.starting_location_url,
        end_location_name=source_event.end_location_name,
        end_location_url=source_event.end_location_url,
        available_canoes=source_event.available_canoes,
        price_per_canoe_sek=source_event.price_per_canoe_sek,
        max_canoes_per_booking=source_event.max_canoes_per_booking,
        weather_forecast_days_before_event=source_event.weather_forecast_days_before_event,
        weather_latitude=source_event.weather_latitude,
        weather_longitude=source_event.weather_longitude,
        faq_booking_text=source_event.faq_booking_text,
        faq_changes_and_questions_text=source_event.faq_changes_and_questions_text,
        rules_on_the_water_text=source_event.rules_on_the_water_text,
        rules_after_paddling_text=source_event.rules_after_paddling_text,
        contact_email=source_event.contact_email,
        contact_phone=source_event.contact_phone,
        is_active=False,
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
