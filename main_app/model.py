from flask_login import UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import validates
from main_app.misc import reverse_geocoding_blocking
from datetime import datetime

from app import db
from settings import MAX_EMAIL_LENGTH, MAX_NAME_LENGTH, MAX_SURNAME_LENGTH, MAX_URL_LENGTH

association_user_ride = db.Table(
    'association_user_ride', db.metadata,
    db.Column('left_id', db.Integer, db.ForeignKey(f'user.id')),
    db.Column('right_id', db.Integer, db.ForeignKey('ride.id'))
)

association_user_organization = db.Table(
    'association_user_organization', db.metadata,
    db.Column('left_id', db.Integer, db.ForeignKey('user.id', ondelete='cascade')),
    db.Column('right_id', db.Integer, db.ForeignKey('organization.id', ondelete='cascade'))
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

    @hybrid_property
    def rating(self):
        # TODO: implementation
        return 5.0

    def check_password(self, password):
        return check_password_hash(self.password, password)


class JoinRideRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ride_id = db.Column(db.Integer, db.ForeignKey('ride.id'), nullable=False)
    # 0 - no answer, 1 - accepted, -1 - declined
    status = db.Column(db.Integer, nullable=False, server_default='0')


class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(600), nullable=False, server_default='undefined')
    description = db.Column(db.String(600))
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, server_default='1')
    creator = db.relationship('User')
    control_question = db.Column(db.String(400), nullable=False, server_default='undefined')
    control_answer = db.Column(db.String(200), nullable=False, server_default='undefined')
    users = db.relationship('User', secondary=association_user_organization,
                            backref='organizations',
                            cascade='all, delete',
                            passive_deletes=True
                            )
    photo_url = db.Column(db.String(MAX_URL_LENGTH))

    @validates('creator')
    def ensure_is_member(self, key, value):
        if value not in self.users:
            self.users.append(value)
        return value

    @hybrid_property
    def last_ride_datetime(self):
        return max([x.submit_datetime for x in self.is_start_for]) if self.is_start_for else '-'

    @hybrid_property
    def total_members(self):
        return len(self.users)

    @hybrid_property
    def total_drivers(self):
        return sum([len(user.cars) > 0 for user in self.users])

    @hybrid_property
    def min_ride_cost(self):
        return min([x.price for x in self.is_start_for]) if self.is_start_for else '-'

    @hybrid_property
    def max_ride_cost(self):
        return max([x.price for x in self.is_start_for]) if self.is_start_for else '-'


class Ride(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    start_organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    start_organization = db.relationship(
        'Organization', backref='is_start_for', foreign_keys=[start_organization_id])

    stop_latitude = db.Column(db.Float, nullable=False)
    stop_longitude = db.Column(db.Float, nullable=False)
    submit_datetime = db.Column(db.DateTime, server_default=datetime.now().isoformat())

    total_seats = db.Column(db.Integer, server_default='4', nullable=False)
    host_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    host = db.relationship('User', backref='hosted_rides')
    passengers = db.relationship('User', secondary=association_user_ride, backref='all_rides')

    is_active = db.Column(db.Boolean, nullable=False, server_default='true')

    price = db.Column(db.Float, nullable=False, server_default='0')
    car_id = db.Column(db.Integer, db.ForeignKey('car.id'), nullable=False, server_default='2')
    car = db.relationship('Car')
    description = db.Column(db.String(600))

    @hybrid_property
    def free_seats(self):
        return self.total_seats - len(self.passengers)

    @hybrid_property
    def stop_address(self):
        return reverse_geocoding_blocking(
            latitude=self.stop_latitude, longitude=self.stop_longitude
        )['address']

    @hybrid_property
    def is_mine(self):
        return self.host == current_user


class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(100), nullable=False)
    registry_number = db.Column(db.String(20), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    owner = db.relationship('User', backref='cars')
