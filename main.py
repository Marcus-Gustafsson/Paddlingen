
import os
import random
from util.helper_functions import get_images_for_year
from flask import Flask, render_template, request, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)    # Create a new Flask web app
app.config.from_pyfile('config.py')  # Load settings
db = SQLAlchemy(app)

class RentForm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=False, nullable=False)
    #bookedCount = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"Bokning('{self.id}', '{self.name}')"

with app.app_context():
    db.create_all()
@app.route("/")  # The homepage

def index():
    alla_bokningar = RentForm.query.order_by(RentForm.id).all()
    # 6. Pass them into the template. Jinja will loop over each list to build the grid.
    return render_template("index.html",
                           pics2024=get_images_for_year("2024"),
                           pics2023=get_images_for_year("2023"),
                           pics2022=get_images_for_year("2022"),
                           bokningar=alla_bokningar)

@app.route('/create-checkout-session', methods=['POST'])
def payment():
    count = int(request.form['canoeCount'])
    names = []
    for i in range(1, count+1):
        first = request.form.get(f'canoe{i}_fname', '').strip()
        last  = request.form.get(f'canoe{i}_lname', '').strip()
        full  = f"{first} {last}".strip()
        # fallback if they left both blank
        names.append(full or f"Unnamed person #{i}")

    session['pending_booking'] = {
    'names': names,
    'canoe_count': count
    }

    return redirect(url_for('paymentSuccess'))

@app.route('/payment-success')
def paymentSuccess():
    data = session.pop('pending_booking', None)
    if not data:
        return redirect(url_for('index'))


    for person_name in data['names']:
        booking = RentForm(name=person_name)
        db.session.add(booking)

    db.session.commit()
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run()   # Starts Flask on http://127.0.0.1:5000

