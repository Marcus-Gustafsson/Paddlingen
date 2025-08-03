"""
Canoe Rental Booking System

This is a Flask web application for managing canoe rental bookings.
Users can view available canoes, make bookings, and see existing bookings.

Flask is a lightweight web framework for Python that helps you build web applications.
"""

import logging
from util.helper_functions import get_images_for_year
from flask import Flask, render_template, request, session, redirect, url_for, jsonify, flash, make_response
import requests
from flask_wtf import CSRFProtect
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from util.db_models import db, RentForm, User, PendingBooking
import json

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

###############################################################################
#  APP OBJECT
#  ----------------------------------------------------------------------------
#  We build a single “app” instance that represents our entire web application.
#  • Flask(__name__) tells Flask where to look for templates/static files
#    (it uses the current file’s location).
#  • app.config.from_pyfile('config.py') pulls in ALL settings (DB path,
#    SECRET_KEY, etc.) before the first request is ever handled.
###############################################################################
app = Flask(__name__)
app.config.from_pyfile('config.py')

###############################################################################
#  FLASK EXTENSIONS
#  ----------------------------------------------------------------------------
#  Flask by itself is tiny.  We “bolt on” extra power via extensions:
#    • SQLAlchemy (db)        – ORM → turns Python classes <-> DB tables
#    • CSRFProtect            – adds hidden tokens to every POST form
#    • LoginManager           – handles user sessions / @login_required
#  Each extension gets passed the app so it can read our config and register
#  itself with Flask’s request/response cycle.
###############################################################################
db.init_app(app)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# ----------------------------------------------------------------------------
# RATE LIMITER
# ----------------------------------------------------------------------------
# We use Flask-Limiter to prevent brute-force and abuse of our endpoints.
# • key_func=get_remote_address will track limits per IP address.
# • default_limits apply to all routes unless overridden.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
limiter.init_app(app)   # Wire the limiter into our Flask app


# ----------------------------------------------------------------------------
# BUSINESS RULES
# ----------------------------------------------------------------------------
# We never want to rent more than MAX_CANOEES at once.
# We load it from config so it’s easy to change in one spot.
MAX_CANOEES = app.config.get('MAX_CANOEES', 50)


# Flask needs an “application context” to know which app’s settings to use.
# Wrapping create_all() in `with app.app_context():` makes sure the ORM can
# see app.config['SQLALCHEMY_DATABASE_URI'] before it tries to touch the DB.
with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    """
    Flask-Login callback: load the User object for this user_id
    using the new Session.get() style (SQLAlchemy 2.0+).
    """
    # db.session.get(ModelClass, primary_key) is the new recommended API
    return db.session.get(User, int(user_id))


@app.route("/")
def index():
    """
    Homepage route handler.
    We also calculate how many canoes are still free (MAX_CANOEES – current bookings)
    and send that to the template for client‐side dropdown limiting.
    """
    # fetch all bookings for your overview panel
    alla_bokningar = RentForm.query.order_by(RentForm.id).all()

    # server‐side business rule from config
    current = RentForm.query.count()
    available_canoes = max(0, MAX_CANOEES - current)

    return render_template(
      "index.html",
      pics2019_earlier=get_images_for_year("2019_&_tidigare"),
      pics2020=get_images_for_year("2020"),
      pics2021=get_images_for_year("2021"),
      pics2022=get_images_for_year("2022"),
      pics2023=get_images_for_year("2023"),
      pics2024=get_images_for_year("2024"),
      pics2025=get_images_for_year("2025"),
      bokningar=alla_bokningar,
      available_canoes=available_canoes
    )

@app.route('/create-checkout-session', methods=['POST'])
@limiter.limit("10 per minute")
def payment():
    """
    1) Parse requested canoe count
    2) Check how many are already booked
    3) If they ask for more than available → reject immediately
    4) Otherwise create a PendingBooking record and proceed to paymentSuccess

    Storing the booking server-side means the customer cannot modify the
    canoe count or the participant names by editing their browser cookie.
    """
    # 1) get requested quantity
    try:
        requested = int(request.form['canoeCount'])
    except (ValueError, KeyError):
        flash("Ogiltigt antal kanoter.", 'error')
        return redirect(url_for('index'))

    # 2) count existing bookings
    current = RentForm.query.count()
    available = MAX_CANOEES - current

    # 3) if they want too many, stop here
    # Log the requested and available canoe counts for debugging purposes.
    # These debug messages only appear when the logging level is set to DEBUG.
    logger.debug("User requested %d canoe(s)", requested)
    logger.debug("Canoes available before booking: %d", available)
    if requested > available:
        flash(
          f"Tyvärr, bara {available} kanot(er) kvar. Vänligen minska din beställning.",
          'error'
        )
        return redirect(url_for('index'))

    # 4) build names list as before
    names = []
    for i in range(1, requested + 1):
        first = request.form.get(f'canoe{i}_fname', '').strip()
        last  = request.form.get(f'canoe{i}_lname', '').strip()
        names.append((f"{first} {last}").strip() or f"Unnamed person #{i}")

    # Create a PendingBooking row in the database. Only the resulting id is
    # stored in the user session so the visitor cannot tamper with the
    # actual booking details.
    pending = PendingBooking(
        canoe_count=requested,
        participant_names=json.dumps(names),
        status='pending'
    )
    db.session.add(pending)
    db.session.commit()  # commit to assign an id

    session['pending_booking_id'] = pending.id
    return redirect(url_for('paymentSuccess'))

@app.route('/payment-success')
def paymentSuccess():
    """
    Finalize the booking after (simulated) payment.

    Steps:
        1. Look up the PendingBooking referenced in the user's session.
        2. Re-check availability to avoid overbooking.
        3. Convert the pending record into permanent RentForm entries.
        4. Remove the PendingBooking row.

    By storing only the database ID in the session and the actual booking
    details on the server we prevent clients from tampering with their
    reservations.
    """
    pending_id = session.pop('pending_booking_id', None)
    if not pending_id:
        # No reference → user reloaded or came here directly
        return redirect(url_for('index'))

    pending = db.session.get(PendingBooking, pending_id)
    if not pending:
        return redirect(url_for('index'))

    requested = pending.canoe_count
    names = json.loads(pending.participant_names)
    current = RentForm.query.count()
    if current + requested > MAX_CANOEES:
        flash(
          "Ojdå! Någon hann boka före dig. Försök igen med färre kanoter.",
          'error'
        )
        db.session.delete(pending)
        db.session.commit()
        return redirect(url_for('index'))

    # Mark as paid for auditing, then create one RentForm per participant.
    pending.status = 'paid'
    for name in names:
        booking = RentForm(name=name, transaction_id="12345abcdefg")
        db.session.add(booking)

    # Remove the temporary pending booking now that it is confirmed.
    db.session.delete(pending)
    db.session.commit()

    return redirect(url_for('index'))

@app.route('/api/booking-count')
def get_booking_count():
    """
    API endpoint that returns the current number of bookings.
    
    This route:
    1. Counts all bookings in the database
    2. Returns the count as JSON data
    
    The JavaScript fetch() function will call this endpoint.
    
    Returns:
        JSON object with the count: {"count": 25}
    """
    # Count all rows in the RentForm table
    # .count() is a SQLAlchemy method that counts database records
    booking_count = RentForm.query.count()
    
    # Return the count as JSON
    # jsonify() converts Python data to JSON format that JavaScript can read
    return jsonify({'count': booking_count})



@app.route('/login', methods=['GET','POST'])
@limiter.limit("5 per minute")   # max 5 login attempts per minute per IP
def login():
    """
    Displays and handles the login form.
    On GET: render the form.
    On POST: validate credentials, call login_user(), then redirect.
    """
    if current_user.is_authenticated:
        # Already logged in? Go to admin dashboard.
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            # Log in this user (stores user.id in session)
            login_user(user)
            flash('Inloggning lyckades!', 'success')
            # next = redirect target from ?next=...
            next_page = request.args.get('next') or url_for('admin_dashboard')
            return redirect(next_page)
        else:
            flash('Felaktigt användarnamn eller lösenord', 'error')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Logs out the current user and redirects to login."""
    logout_user()
    flash('Du har loggats ut.', 'info')
    return redirect(url_for('login'))



# === Coordinates for your specific event location ===
LAT = 59.866580523479584
LON = 14.850996977247622

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

@app.route('/api/forecast')
def get_forecast():
    """
    Flask route to fetch weather forecast for a specific date.
    Tries to get data starting at 10:00 UTC, and uses next 6 hours forecast.
    If 10:00 is unavailable, uses 12:00 UTC as fallback.
    Returns temperature, rain amount and weather icon.
    """
    headers = {
        "User-Agent": "PaddlingenEventApp/1.0 (contact@example.com)"  # Required by MET API
    }
    params = {
        "lat": LAT,
        "lon": LON
    }

    target_date = request.args.get("date")
    if not target_date:
        return jsonify({"error": "Missing required 'date' parameter (YYYY-MM-DD)."}), 400

    try:
        response = requests.get(MET_API_URL, headers=headers, params=params)
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
            return jsonify({"error": "No forecast available at 10:00 or 12:00 UTC for this date."}), 404

        # Extract details
        temp = selected_entry["data"]["instant"]["details"].get("air_temperature")
        rain = selected_entry["data"].get("next_6_hours", {}).get("details", {}).get("precipitation_amount", 0)
        symbol_code = selected_entry["data"].get("next_6_hours", {}).get("summary", {}).get("symbol_code", "cloudy")
        base_symbol = symbol_code.split("_")[0]

        forecast = {
            "temperature": round(temp) if temp is not None else "N/A",
            "rainChance": str(rain).replace(".",","),  # simple approximation
            "icon": WEATHER_EMOJIS.get(base_symbol, "☁️")
        }
        return jsonify(forecast)
        

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    


@app.route('/admin')
@login_required
def admin_dashboard():
    """
    Shows the admin dashboard page.

    • Queries all RentForm bookings, ordered by ID.
    • Renders templates/admin.html, passing the booking list.
    """
    bookings = RentForm.query.order_by(RentForm.id).all()
    return render_template('admin.html', bookings=bookings)


@app.route('/admin/add', methods=['POST'])
@login_required
def admin_add():
    """
    Handles the "Add new booking" form submission.

    • Reads `name` from form data, strips whitespace.
    • If non-empty, creates & commits a new RentForm record.
    • Redirects back to the dashboard.
    """
    # Get the 'name' field, defaulting to empty string
    name = request.form.get('name', '').strip()
    if name:
        db.session.add(RentForm(name=name, transaction_id="12345678910"))
        db.session.commit()
    # Always redirect (PRG pattern—Prevents resubmission on refresh)
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/update/<int:id>', methods=['POST'])
@login_required
def admin_update(id):
    """
    Handles editing an existing booking’s name.

    • Fetches the RentForm record by `id` or 404s.
    • Reads the new `name`, strips whitespace.
    • If non-empty, updates record & commits.
    • Redirects back to dashboard.
    """
    booking = RentForm.query.get_or_404(id)
    new_name = request.form.get('name', '').strip()
    if new_name:
        booking.name = new_name
        db.session.commit()
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/delete/<int:id>', methods=['POST'])
@login_required
def admin_delete(id):
    """
    Handles deletion of a booking.

    • Fetches the RentForm record by `id` or 404s.
    • Deletes it, commits the transaction.
    • Redirects back to dashboard.
    """
    booking = RentForm.query.get_or_404(id)
    db.session.delete(booking)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))


@app.errorhandler(429)
def ratelimit_handler(e):
    """
    Custom handler for rate limit errors (HTTP 429).
    We return a friendly JSON or HTML message.
    """
    # If the client expects JSON:
    if request.path.startswith('/api/'):
        return jsonify(error="Too many requests, please try again later."), 429
    # Otherwise render a template or plain text:
    return make_response(
        "Too many requests. Please slow down and try again in a few minutes.",
        429
    )

# This block only runs if you execute this file directly (not when imported)
if __name__ == "__main__":
    # Start the Flask development server
    # By default, it runs on http://127.0.0.1:5000
    # In production, you'd use a proper web server instead of app.run()
    app.run()