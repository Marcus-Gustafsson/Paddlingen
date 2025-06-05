from main import app, db
from main import RentForm
with app.app_context():
    db.create_all()
    RentForm1 = RentForm(firstName='Regen', lastName='Figga')
    db.session.add(RentForm1)
    db.session.commit()
    RentForm.query.all()