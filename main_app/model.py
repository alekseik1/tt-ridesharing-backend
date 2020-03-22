from flask_login import UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.hybrid import hybrid_property
from main_app.misc import reverse_geocoding_blocking

from app import db
from settings import MAX_EMAIL_LENGTH, MAX_NAME_LENGTH, MAX_SURNAME_LENGTH, MAX_URL_LENGTH

association_user_ride = db.Table(
    'association_user_ride', db.metadata,
    db.Column('left_id', db.Integer, db.ForeignKey(f'user.id')),
    db.Column('right_id', db.Integer, db.ForeignKey('ride.id'))
)

association_user_organization = db.Table(
    'association_user_organization', db.metadata,
    db.Column('left_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('right_id', db.Integer, db.ForeignKey('organization.id'))
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(MAX_NAME_LENGTH), nullable=False)
    last_name = db.Column(db.String(MAX_SURNAME_LENGTH), nullable=False)
    email = db.Column(db.String(MAX_EMAIL_LENGTH), nullable=False, unique=True)
    photo_url = db.Column(db.String(MAX_URL_LENGTH))
    phone_number = db.Column(db.String(20), server_default='+71111111111', nullable=False)
    _password_hash = db.Column(db.String(94), nullable=False)

    @hybrid_property
    def password(self):
        return self._password_hash

    @password.setter
    def password(self, value):
        self._password_hash = generate_password_hash(value)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    address = db.Column(db.String(600))
    description = db.Column(db.String(600))
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, server_default='1')
    creator = db.relationship('User')
    users = db.relationship('User', secondary=association_user_organization,
                            backref='organizations', passive_deletes=True)
    photo_url = db.Column(db.String(MAX_URL_LENGTH))


class Ride(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    start_organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    start_organization = db.relationship(
        'Organization', backref='is_start_for', foreign_keys=[start_organization_id])

    stop_latitude = db.Column(db.Float, nullable=False)
    stop_longitude = db.Column(db.Float, nullable=False)

    total_seats = db.Column(db.Integer, server_default='4', nullable=False)
    host_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    passengers = db.relationship('User', secondary=association_user_ride, backref='all_rides')

    price = db.Column(db.Float)
    car_id = db.Column(db.Integer, db.ForeignKey('car.id'), nullable=False, server_default='2')
    description = db.Column(db.String(600))

    @hybrid_property
    def stop_address(self):
        return reverse_geocoding_blocking(
            latitude=self.stop_latitude, longitude=self.stop_longitude
        )['address']

    @hybrid_property
    def is_mine(self):
        return self.host_driver_id == current_user.id


class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(100), nullable=False)
    registry_number = db.Column(db.String(20), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    owner = db.relationship('User', backref='cars')
