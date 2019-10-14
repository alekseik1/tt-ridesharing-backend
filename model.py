from app import db, ma, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from marshmallow import fields

MAX_NAME_LENGTH = 40
MAX_SURNAME_LENGTH = 40
MAX_EMAIL_LENGTH = 256
MAX_URL_LENGTH = 2000


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(MAX_NAME_LENGTH), nullable=False)
    last_name = db.Column(db.String(MAX_SURNAME_LENGTH), nullable=False)
    email = db.Column(db.String(MAX_EMAIL_LENGTH), nullable=False, unique=True)
    photo = db.Column(db.String(MAX_URL_LENGTH))
    password_hash = db.Column(db.String(94))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login.user_loader
def load_user(id):
    user = User.query.get(int(id))
    if not user:
        return None
    return user


class RegisterUserSchema(ma.ModelSchema):
    class Meta:
        model = User
    password = fields.String(required=True)


class Driver(db.Model):
    id = db.Column(db.Integer, db.ForeignKey(User.__tablename__ + '.id'), primary_key=True)
    passport_1 = db.Column(db.String(MAX_URL_LENGTH), nullable=False)
    passport_2 = db.Column(db.String(MAX_URL_LENGTH), nullable=False)
    passport_selfie = db.Column(db.String(MAX_URL_LENGTH), nullable=False)
    driver_license_1 = db.Column(db.String(MAX_URL_LENGTH), nullable=False)
    driver_license_2 = db.Column(db.String(MAX_URL_LENGTH), nullable=False)


class RegisterDriverSchema(ma.ModelSchema):
    user_id = fields.Integer(required=True)
    passport_url_1 = fields.String(required=True)
    passport_url_2 = fields.String(required=True)
    passport_url_selfie = fields.String(required=True)
    license_1 = fields.String(required=True)
    license_2 = fields.String(required=True)


class DriverSchema(ma.ModelSchema):
    class Meta:
        model = Driver
