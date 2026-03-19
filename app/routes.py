"""Canoe Rental Booking System.

This module contains all route and view functions for the application.
Routes are attached to a :class:`~flask.Blueprint` so they can be
registered by the application factory.
"""

import logging
from datetime import timedelta
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
    session,
    url_for,
)
from flask_login import (  # type: ignore[import-untyped]
    current_user,
    login_required,
    login_user,
    logout_user,
)

from .util.event_settings import (
    build_event_settings_with_fallback,
    get_active_event,
    get_available_canoes_total_with_fallback,
    get_event_year_with_fallback,
    get_max_canoes_per_booking_with_fallback,
    get_price_per_canoe_with_fallback,
    get_weather_coordinates_with_fallback,
)
from .util.helper_functions import get_previous_year_image_filenames
from .util.db_models import BookedCanoe, BookingOrder, User, db, get_current_utc_time
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

main_blueprint = Blueprint("main", __name__)


def get_total_available_canoes() -> int:
    """Return the active event's total number of available canoes.

    Returns:
        int: Total number of canoes available for the active event. When the
        database has no active event row, the value falls back to ``config.py``.
    """

    return get_available_canoes_total_with_fallback()


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


def build_previous_year_gallery_data() -> tuple[list[str], list[str]]:
    """Build ribbon and gallery image URLs for previous-year photos.

    Returns:
        tuple[list[str], list[str]]: Two lists of static image URLs.
        The first list is used by the homepage ribbon.
        The second list contains the full combined gallery used by the image
        viewer modal. For now both lists contain the same images because the
        ribbon should loop through all available previous-year photos.
    """
    image_filenames = get_previous_year_image_filenames()
    image_urls = [
        url_for("static", filename=f"images/previous_years/{image_filename}")
        for image_filename in image_filenames
    ]
    return image_urls, image_urls


def get_event_coordinates() -> tuple[float, float]:
    """Return the configured latitude and longitude for the event location.

    Returns:
        tuple[float, float]: Event latitude and longitude used by the weather
        forecast integration.
    """

    return get_weather_coordinates_with_fallback()


@main_blueprint.route("/")
def index():
    """Homepage route handler.

    We also calculate how many canoes are still free and send that to the
    template for client-side dropdown limiting.
    """
    # fetch all bookings for your overview panel
    alla_bokningar = get_confirmed_booked_canoes_query().order_by(BookedCanoe.id).all()

    # server‐side business rule from config
    current = count_confirmed_booked_canoes()
    available_canoes = max(0, get_total_available_canoes() - current)
    event_settings = build_event_settings()
    (
        previous_year_ribbon_image_urls,
        previous_year_gallery_image_urls,
    ) = build_previous_year_gallery_data()

    return render_template(
        "index.html",
        bokningar=alla_bokningar,
        available_canoes=available_canoes,
        event_settings=event_settings,
        previous_year_ribbon_image_urls=previous_year_ribbon_image_urls,
        previous_year_gallery_image_urls=previous_year_gallery_image_urls,
    )


@main_blueprint.route("/create-checkout-session", methods=["POST"])
@rate_limiter.limit("10 per minute")
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

    participant_names = build_participant_names_from_form(requested)
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
        return redirect(url_for("main.admin_dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            # Log in this user (stores user.id in session)
            login_user(user)
            flash("Inloggning lyckades!", "success")
            # next = redirect target from ?next=...
            next_page = request.args.get("next") or url_for("main.admin_dashboard")
            return redirect(next_page)
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

    • Queries confirmed `BookedCanoe` rows for the active event when available.
    • Renders ``templates/admin.html``, passing the booking list.
    """
    bookings = get_confirmed_booked_canoes_query().order_by(BookedCanoe.id).all()
    return render_template("admin.html", bookings=bookings)


@main_blueprint.route("/admin/add", methods=["POST"])
@login_required
def admin_add():
    """Handle the "Add new booking" form submission.

    • Reads ``name`` from form data, strips whitespace.
    • If non-empty, creates a one-canoe manual booking order and canoe row.
    • Redirects back to the dashboard.
    """
    name = request.form.get("name", "").strip()
    if name:
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
            payment_provider="admin_manual",
            paid_at=get_current_utc_time(),
        )
        db.session.add(booking_order)
        db.session.flush()
        booking_order.public_booking_reference = build_public_booking_reference(
            booking_order.id
        )

        booked_canoe = BookedCanoe(
            booking_order_id=booking_order.id,
            participant_first_name="",
            participant_last_name="",
            status="confirmed",
        )
        booked_canoe.name = name
        db.session.add(booked_canoe)
        db.session.commit()

    return redirect(url_for("main.admin_dashboard"))


@main_blueprint.route("/admin/update/<int:id>", methods=["POST"])
@login_required
def admin_update(id):
    """Handle editing an existing booking's name.

    • Fetches the ``BookedCanoe`` record by ``id`` or 404s.
    • Reads the new ``name``, strips whitespace.
    • If non-empty, updates the record and commits.
    • Redirects back to the dashboard.
    """
    booking = db.session.get(BookedCanoe, id)
    if booking is None:
        abort(404)
    new_name = request.form.get("name", "").strip()
    if new_name:
        booking.name = new_name
        db.session.commit()
    return redirect(url_for("main.admin_dashboard"))


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
    return redirect(url_for("main.admin_dashboard"))


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
