"""
Canoe Rental Booking System

This is a Flask web application for managing canoe rental bookings.
Users can view available canoes, make bookings, and see existing bookings.

Flask is a lightweight web framework for Python that helps you build web applications.
"""


from util.helper_functions import get_images_for_year
from flask import Flask, render_template, request, session, redirect, url_for, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
import requests
from collections import Counter
from functools import wraps

# Create a new Flask web application instance
# __name__ tells Flask where to look for templates and static files
app = Flask(__name__)    

# Load configuration settings from a separate config.py file
# This keeps sensitive data (like database credentials) separate from your code
app.config.from_pyfile('config.py')  

# Initialize SQLAlchemy - this is an ORM (Object Relational Mapper)
# It lets us work with databases using Python objects instead of SQL queries
db = SQLAlchemy(app)

class RentForm(db.Model):
    """
    Database model for rental bookings.
    
    This class represents a table in our database where each row is a booking.
    SQLAlchemy will automatically create a table based on this class definition.
    
    Attributes:
        id: Unique identifier for each booking (automatically increments)
        name: The name of the person making the booking
    """
    # Primary key = unique identifier for each record
    id = db.Column(db.Integer, primary_key=True)
    
    # String column that can hold up to 120 characters
    # nullable=False means this field is required (can't be empty)
    name = db.Column(db.String(120), unique=False, nullable=False)
    
    # This commented line could track how many canoes were booked
    #bookedCount = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        """
        Special method that defines how a booking object is displayed.
        This is useful for debugging - when you print a booking, you'll see this format.
        
        Returns:
            String representation of the booking
        """
        return f"Bokning('{self.id}', '{self.name}')"

# This ensures database operations happen within the app's context
# app.app_context() is needed when working with the database outside of a request
with app.app_context():
    # Create all database tables based on the models we've defined
    # This only creates tables that don't already exist
    db.create_all()


# Route decorator - tells Flask what URL should trigger this function
@app.route("/")  # The homepage (root URL)
def index():
    """
    Homepage route handler.
    
    This function runs when someone visits the main page of your website.
    It fetches all bookings from the database and displays them along with photos.
    
    Returns:
        Rendered HTML template with booking data and images
    """
    # Query the database for all bookings, ordered by ID
    # .query accesses the table, .order_by() sorts results, .all() gets all records
    alla_bokningar = RentForm.query.order_by(RentForm.id).all()
    
    # render_template() combines an HTML template with data
    # The template can access these variables: pics2024, pics2023, pics2022, bokningar
    return render_template("index.html",
                           pics2019_earlier=get_images_for_year("2019_&_tidigare"),
                           pics2020=get_images_for_year("2020"),
                           pics2021=get_images_for_year("2021"),
                           pics2022=get_images_for_year("2022"),
                           pics2023=get_images_for_year("2023"),
                           pics2024=get_images_for_year("2024"),
                           bokningar=alla_bokningar)

# This route only accepts POST requests (form submissions)
@app.route('/create-checkout-session', methods=['POST'])
def payment():
    """
    Handles the booking form submission.
    
    This function processes the canoe rental form when submitted.
    It collects all the names entered and stores them temporarily in the session
    before redirecting to the payment success page.
    
    The session is like a temporary storage that remembers data between page loads
    for each user.
    
    Returns:
        Redirect to the payment success page
    """
    # Get the number of canoes from the form data
    # request.form contains all data submitted from an HTML form
    count = int(request.form['canoeCount'])
    
    # List to store all the names
    names = []
    
    # Loop through each canoe to get the person's name
    # range(1, count+1) gives us numbers from 1 to count (inclusive)
    for i in range(1, count+1):
        # Get first name from form field, remove extra spaces with strip()
        # .get() is safer than [] because it won't crash if the field is missing
        first = request.form.get(f'canoe{i}_fname', '').strip()
        last  = request.form.get(f'canoe{i}_lname', '').strip()
        
        # Combine first and last name
        full  = f"{first} {last}".strip()
        
        # If no name was provided, create a default name
        # The 'or' operator returns the first truthy value
        names.append(full or f"Unnamed person #{i}")

    # Store booking data in session (temporary storage)
    # This data will be available on the next page
    session['pending_booking'] = {
        'names': names,
        'canoe_count': count
    }

    # Redirect to the payment success page
    # url_for() generates the URL for a given function name
    return redirect(url_for('paymentSuccess'))

@app.route('/payment-success')
def paymentSuccess():
    """
    Handles successful payment completion.
    
    This function runs after payment is complete. It retrieves the booking data
    from the session, saves it to the database, and redirects back to the homepage.
    
    If no booking data is found (e.g., someone navigates directly to this URL),
    it redirects to the homepage.
    
    Returns:
        Redirect to the homepage
    """
    # Get and remove booking data from session
    # .pop() gets the value and removes it (so it can't be used twice)
    # If 'pending_booking' doesn't exist, it returns None
    data = session.pop('pending_booking', None)
    
    # If no booking data found, redirect to homepage
    if not data:
        return redirect(url_for('index'))

    # Create a database entry for each person
    for person_name in data['names']:
        # Create a new RentForm object (this represents a row in the database)
        booking = RentForm(name=person_name)
        
        # Add this booking to the database session (not saved yet)
        db.session.add(booking)

    # Save all the bookings to the database
    # commit() actually writes the changes to the database
    db.session.commit()
    
    # Redirect back to the homepage where they can see their booking
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
    
# --- after app.config.from_pyfile('config.py') ---
ADMIN_USERNAME = app.config['ADMIN_USERNAME']
ADMIN_PASSWORD = app.config['ADMIN_PASSWORD']

def admin_required(f):
    """
    Decorator to protect admin routes with HTTP Basic Auth.

    Checks the Authorization header for a username/password
    that match ADMIN_USERNAME and ADMIN_PASSWORD. If not present
    or incorrect, returns a 401 asking the browser to prompt for credentials.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # request.authorization holds HTTP Basic credentials
        auth = request.authorization
        # If missing or wrong, challenge the client
        if not auth or auth.username != ADMIN_USERNAME or auth.password != ADMIN_PASSWORD:
            return Response(
                'Authentication required',    # message body
                401,                          # HTTP 401 Unauthorized
                {'WWW-Authenticate': 'Basic realm="Admin Area"'}  # prompt header
            )
        # Credentials OK—proceed to handler
        return f(*args, **kwargs)
    return decorated


@app.route('/admin')
@admin_required
def admin_dashboard():
    """
    Shows the admin dashboard page.

    • Queries all RentForm bookings, ordered by ID.
    • Renders templates/admin.html, passing the booking list.
    """
    bookings = RentForm.query.order_by(RentForm.id).all()
    return render_template('admin.html', bookings=bookings)


@app.route('/admin/add', methods=['POST'])
@admin_required
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
        db.session.add(RentForm(name=name))
        db.session.commit()
    # Always redirect (PRG pattern—Prevents resubmission on refresh)
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/update/<int:id>', methods=['POST'])
@admin_required
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
@admin_required
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

# This block only runs if you execute this file directly (not when imported)
if __name__ == "__main__":
    # Start the Flask development server
    # By default, it runs on http://127.0.0.1:5000
    # In production, you'd use a proper web server instead of app.run()
    app.run()