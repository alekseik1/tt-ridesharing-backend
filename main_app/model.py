from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.hybrid import hybrid_property

from app import db

MAX_NAME_LENGTH = 40
MAX_SURNAME_LENGTH = 40
MAX_EMAIL_LENGTH = 256
MAX_URL_LENGTH = 2000

association_user_ride = db.Table(
    'association_user_ride', db.metadata,
    db.Column('left_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('right_id', db.Integer, db.ForeignKey('ride.id'))
)

association_user_organization = db.Table(
    'association_user_organization', db.metadata,
    db.Column('left_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('right_id', db.Integer, db.ForeignKey('organization.id'))
)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(MAX_NAME_LENGTH), nullable=False)
    last_name = db.Column(db.String(MAX_SURNAME_LENGTH), nullable=False)
    email = db.Column(db.String(MAX_EMAIL_LENGTH), nullable=False, unique=True)
    photo_url = db.Column(db.String(MAX_URL_LENGTH))
    phone_number = db.Column(db.String(20), server_default='+71111111111', nullable=False)
    password_hash = db.Column(db.String(94))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @hybrid_property
    def is_driver(self):
        id = db.session.query(Driver).filter_by(id=self.id).first() is not None
        return id


class Driver(db.Model):
    id = db.Column(db.Integer, db.ForeignKey(User.__tablename__ + '.id'), primary_key=True)
    license_1 = db.Column(db.String(MAX_URL_LENGTH), nullable=False)
    license_2 = db.Column(db.String(MAX_URL_LENGTH), nullable=False)


class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    address = db.Column(db.String(600))
    description = db.Column(db.String(600))
    users = db.relationship('User', secondary=association_user_organization, backref='organizations',
                            passive_deletes=True)


class Ride(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    start_organization = db.relationship('Organization', backref='is_start_for', foreign_keys=[start_organization_id])
    stop_latitude = db.Column(db.Float, nullable=False)
    stop_longitude = db.Column(db.Float, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    # TODO: Очень плохо брать со стороны фронта адрес, а не определять самим
    stop_address = db.Column(db.String(600))
    total_seats = db.Column(db.Integer, server_default='4', nullable=False)
    host_driver_id = db.Column(db.Integer, db.ForeignKey('driver.id'), nullable=False)
    estimated_time = db.Column(db.Time)
    is_available = db.Column(db.Boolean, nullable=False, default=True)
    is_finished = db.Column(db.Boolean, server_default='false', nullable=False, default=False)
    # TODO: Возможно, пользователю не обязательно иметь поле `all_rides`. Тем более, что поездки еще арихвируются
    passengers = db.relationship('User', secondary=association_user_ride, backref='all_rides')
    cost = db.Column(db.Float)
    car_id = db.Column(db.Integer, db.ForeignKey('car.id'), nullable=False, server_default='2')
    description = db.Column(db.String(600))


class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(100), nullable=False)
    registry_number = db.Column(db.String(20), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('driver.id'), nullable=False)
    owner = db.relationship('Driver', backref='cars')
