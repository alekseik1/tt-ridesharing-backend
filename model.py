from app import db, ma, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from marshmallow import fields

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
    photo = db.Column(db.String(MAX_URL_LENGTH))
    password_hash = db.Column(db.String(94))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class UserSchema(ma.ModelSchema):
    class Meta:
        model = User
        exclude = ['password_hash']


class RegisterUserSchema(ma.ModelSchema):
    class Meta:
        model = User
    password = fields.String(required=True)


class Driver(db.Model):
    id = db.Column(db.Integer, db.ForeignKey(User.__tablename__ + '.id'), primary_key=True)
    driver_license_1 = db.Column(db.String(MAX_URL_LENGTH), nullable=False)
    driver_license_2 = db.Column(db.String(MAX_URL_LENGTH), nullable=False)


class RegisterDriverSchema(ma.ModelSchema):
    user_id = fields.Integer(required=True)
    license_1 = fields.String(required=True)
    license_2 = fields.String(required=True)


class DriverSchema(ma.ModelSchema):
    class Meta:
        model = Driver


class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    users = db.relationship('User', secondary=association_user_organization, backref='organizations')


class OrganizationSchema(ma.ModelSchema):
    class Meta:
        model = Organization


class Ride(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    start_organization = db.relationship('Organization', backref='is_start_for', foreign_keys=[start_organization_id])
    stop_latitude = db.Column(db.Float, nullable=False)
    stop_longitude = db.Column(db.Float, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    total_seats = db.Column(db.Integer, server_default='4', nullable=False)
    host_driver_id = db.Column(db.Integer, db.ForeignKey('driver.id'), nullable=False)
    estimated_time = db.Column(db.Time)
    is_available = db.Column(db.Boolean, nullable=False, default=True)
    passengers = db.relationship('User', secondary=association_user_ride, backref='all_rides')
    cost = db.Column(db.Float)
    description = db.Column(db.String(600))


class RideSchema(ma.ModelSchema):
    class Meta:
        model = Ride
        include_fk = True


class JoinRideSchema(ma.ModelSchema):
    ride_id = fields.Integer(required=True)


class CreateRideSchema(ma.ModelSchema):
    start_organization_id = fields.Integer(required=True)
    stop_latitude = fields.Float(required=True)
    stop_longitude = fields.Float(required=True)
    start_time = fields.String(required=True)
    description = fields.String(required=False)
    total_seats = fields.Integer(required=True)
    cost = fields.Float(required=False)


class FindBestRidesSchema(ma.ModelSchema):
    start_date = fields.DateTime(required=False)
    start_organization_id = fields.Integer(required=True)
    destination_latitude = fields.Integer(required=True)
    destination_longitude = fields.Integer(required=True)


class OrganizationIDSchema(ma.ModelSchema):
    organization_id = fields.Integer(required=True)
