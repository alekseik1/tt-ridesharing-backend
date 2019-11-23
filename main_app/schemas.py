from marshmallow import fields, validates, ValidationError
from flask import jsonify
import phonenumbers
from email_validator import validate_email, EmailNotValidError

from app import ma, db
from main_app.model import Ride, User, Organization, Driver, Car
from main_app.responses import SwaggerResponses


def is_valid_phone_number(phone_number):
    try:
        validate_phone_number(phone_number)
    except ValidationError:
        return False
    return True


def validate_phone_number(phone_number):
    """
    Validates phone number via raising exceptions

    :param phone_number: String of number
    :return: A <Phone number> object from `phonenumbers` lib
    :raise: ValidationError
    """
    try:
        number = phonenumbers.parse(phone_number)
        if not phonenumbers.is_valid_number(number):
            raise ValidationError('Invalid phone number')
    except:
        raise ValidationError('Invalid phone number')
    return phone_number


def format_phone_number(phone_number_str):
    number = phonenumbers.parse(phone_number_str)
    return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)


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
        car = db.session.query(Car).filter_by(id=car_id).first()
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
    is_driver = fields.Boolean()
    organizations = fields.Nested(OrganizationSchema, many=True)


class UserSchemaNoOrganizations(ma.ModelSchema):
    class Meta:
        model = User
        include_fk = True
        exclude = ['password_hash', 'all_rides']


class UserIDSchema(ma.ModelSchema):
    user_id = fields.Integer(required=True)


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
    email = fields.Email(required=True)
    password = fields.String(required=True)

    @validates('phone_number')
    def is_phone_like(self, phone_number):
        return format_phone_number(validate_phone_number(phone_number))

    @validates('email')
    def email_is_not_in_db(self, email):
        user = db.session.query(User).filter_by(email=email).first()
        if user:
            raise ValidationError('Email is already registered')
        return email


class ChangePhoneSchema(ma.ModelSchema):
    phone_number = fields.String(required=True)

    @validates('phone_number')
    def is_phone_like(self, phone_number):
        return format_phone_number(validate_phone_number(phone_number))


class ChangeNameSchema(ma.ModelSchema):
    first_name = fields.String(required=True)

    @validates('first_name')
    def is_not_none(self, name):
        if not name:
            raise ValidationError('Invalid first name')
        return name


class ChangeLastNameSchema(ma.ModelSchema):
    last_name = fields.String(required=True)

    @validates('last_name')
    def is_not_none(self, name):
        if not name:
            raise ValidationError('Invalid last name')
        return name


class ChangeEmailSchema(ma.ModelSchema):
    email = fields.String(required=True)

    @validates('email')
    def is_valid_email(self, email):
        try:
            email = validate_email(email)['email']
        except EmailNotValidError:
            raise ValidationError('Invalid email')
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
