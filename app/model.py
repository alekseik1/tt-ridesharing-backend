from app import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40))
    surname = db.Column(db.String(40))
    email = db.Column(db.String(256))
    photo_url = db.Column(db.String(2000))
