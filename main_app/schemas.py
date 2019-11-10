from marshmallow import fields, validates, ValidationError
from flask import jsonify

from app import ma, db
from main_app.model import Ride, User, Organization, Driver, Car
from main_app.responses import SwaggerResponses


class FindBestRidesSchema(ma.ModelSchema):
    start_date = fields.DateTime(required=False)
    start_organization_id = fields.Integer(required=True)
    destination_latitude = fields.Integer(required=True)
    destination_longitude = fields.Integer(required=True)


class OrganizationIDSchema(ma.ModelSchema):
    organization_id = fields.Integer(required=True)


class CreateRideSchema(ma.ModelSchema):
    start_organization_id = fields.Integer(required=True)
    stop_latitude = fields.Float(required=True)
    stop_longitude = fields.Float(required=True)
    stop_address = fields.String(required=False)
    start_time = fields.String(required=True)
    description = fields.String(required=False)
    total_seats = fields.Integer(required=True)
    cost = fields.Float(required=False)
    car_id = fields.Integer(required=True)

    @validates('start_time')
    def is_not_empty(self, value):
        if len(value) == 0:
            raise ValidationError('Should not be empty string')

    @validates('car_id')
    def car_exists(self, car_id):
        car = db.sesion.query(Car).filter_by(id=car_id).first()
        if not car:
            raise ValidationError('Invalid car')


class JoinRideSchema(ma.ModelSchema):
    ride_id = fields.Integer(required=True)


class RideSchema(ma.ModelSchema):
    class Meta:
        model = Ride
        include_fk = True


class OrganizationSchema(ma.ModelSchema):
    class Meta:
        model = Organization
        exclude = ['is_start_for']


class UserSchema(ma.ModelSchema):
    class Meta:
        model = User
        include_fk = True
        exclude = ['password_hash', 'all_rides']
    organizations = fields.Nested(OrganizationSchema, many=True)


class DriverSchema(ma.ModelSchema):
    class Meta:
        model = Driver


class RegisterDriverSchema(ma.ModelSchema):
    id = fields.Integer(required=True)
    license_1 = fields.String(required=True)
    license_2 = fields.String(required=True)

    @validates('id')
    def id_is_not_in_db(self, id):
        driver = db.session.query(Driver).filter_by(id=id).first()
        if driver:
            raise ValidationError('Driver is already registered')
        return driver


class RegisterUserSchema(ma.ModelSchema):
    class Meta:
        model = User
    password = fields.String(required=True)

    @validates('email')
    def email_is_not_in_db(self, email):
        user = db.session.query(User).filter_by(email=email).first()
        if user:
            raise ValidationError('Email is already registered')
        return email


class CarSchema(ma.ModelSchema):
    class Meta:
        model = Car


class RegisterCarForDriverSchema(ma.ModelSchema):
    class Meta:
        model = Car
    # Leave this field only for validation
    owner_id = fields.Integer(required=False)

    @validates('owner_id')
    def owner_exists(self, owner_id):
        if db.session.query(Driver).filter_by(id=owner_id).first() is None:
            error = SwaggerResponses.INVALID_DRIVER_WITH_ID
            error['value'] = owner_id
            return jsonify(error), 400


class CarIdSchema(ma.ModelSchema):
    car_id = fields.Integer(required=True)
