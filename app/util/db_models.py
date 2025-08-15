"""
File: util/db_models.py

What it does:
  - Defines the `db` object (SQLAlchemy) independently of any Flask app.
  - Declares three ORM models:
      • RentForm: stores confirmed canoe rental bookings
      • PendingBooking: temporarily stores booking info waiting for payment
      • User: stores admin user accounts for Flask-Login

Why it’s here:
  - Keeps your database schema definitions separate from application logic.
  - Makes models reusable in other scripts/tests without pulling in the entire app.
"""

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

# -------------------------------------------------------------------
# 1) Create the SQLAlchemy `db` object
#
#    We will bind this to our Flask app later with db.init_app(app).
# -------------------------------------------------------------------
db = SQLAlchemy()


# -------------------------------------------------------------------
# 2) Booking model: one row per canoe rental
# -------------------------------------------------------------------
class RentForm(db.Model):
    """
    ORM model for a canoe rental booking.

    Attributes:
        id              Integer primary key, auto-incremented
        name            Text field (up to 120 chars) for the renter’s name
        transaction_id  Text field for the payment transaction identifier
    """
    __tablename__ = 'rent_form'  # Optional: explicitly set table name

    # Primary key column: unique identifier for each booking
    id = db.Column(db.Integer, primary_key=True)
    # Renter’s name, required
    name = db.Column(db.String(120), nullable=False)
    # Payment transaction ID (e.g. from Stripe), required
    transaction_id = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        """
        Return a developer-friendly string representation of a booking.
        Example: <RentForm 3 – Alice Müller - txn_1AbCDe>
        """
        return f"<RentForm {self.id} – {self.name} – {self.transaction_id}>"


# -------------------------------------------------------------------
# 3) Pending booking model: holds data before payment is confirmed
# -------------------------------------------------------------------
class PendingBooking(db.Model):
    """Temporary storage for a booking awaiting payment.

    In the previous implementation booking details were stored in the
    client's session cookie. Cookies live in the user's browser and can be
    tampered with, so a malicious visitor could change the number of canoes
    or participant names after the checkout step.  By saving the data on the
    server we keep full control over it until the payment is completed.

    Attributes:
        id (int): Primary key.
        canoe_count (int): Number of canoes requested.
        participant_names (str): JSON-encoded list of names.
        status (str): "pending", "paid", etc. (for future extensions).
    """

    __tablename__ = 'pending_booking'

    id = db.Column(db.Integer, primary_key=True)
    canoe_count = db.Column(db.Integer, nullable=False)
    participant_names = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')

    def __repr__(self):
        """Return a readable representation for debugging.

        Returns:
            str: String containing the row ID and the number of canoes
                requested, e.g. ``"<PendingBooking 5 – 2 canoe(s)>"``.
        """

        return f"<PendingBooking {self.id} – {self.canoe_count} canoe(s)>"


# -------------------------------------------------------------------
# 4) Admin user model for Flask-Login
# -------------------------------------------------------------------
class User(db.Model, UserMixin):
    """
    ORM model for an administrator account.

    Inherits from UserMixin to integrate with Flask-Login.

    Attributes:
        id        Integer primary key
        username  Unique login name for the admin
        pw_hash   Password hash (never store plaintext!)
    """
    __tablename__ = 'users'  # Optional: explicitly set table name

    # Primary key column
    id = db.Column(db.Integer, primary_key=True)
    # Unique username, required
    username = db.Column(db.String(80), unique=True, nullable=False)
    # Hashed password, required
    pw_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        """
        Hashes the provided plaintext password and stores it in pw_hash.

        Args:
            password (str): The plaintext password to hash.
        """
        self.pw_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Verifies a plaintext password against the stored password hash.

        Args:
            password (str): The plaintext password to verify.

        Returns:
            bool: True if the password matches the hash, False otherwise.
        """
        return check_password_hash(self.pw_hash, password)

