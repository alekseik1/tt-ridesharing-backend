from app import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40))
    surname = db.Column(db.String(40))
    email = db.Column(db.String(256))
    photo = db.Column(db.String(2000))
    is_trusful = db.Column(db.Boolean)


class Driver(User):
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    passport_1 = db.Column(db.String(2000))
    passport_2 = db.Column(db.String(2000))
    passport_selfie = db.Column(db.String(2000))
    driver_license_1 = db.Column(db.String(2000))
    driver_license_2 = db.Column(db.String(2000))
