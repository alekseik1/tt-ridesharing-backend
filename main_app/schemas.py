from marshmallow import fields, validates, ValidationError, Schema
from flask import jsonify

from app import ma, db
from main_app.model import Ride, User, Organization, Driver, Car
from main_app.controller import check_email, check_phone_number, check_image_url
from main_app.responses import SwaggerResponses


class FindBestRidesSchema(ma.ModelSchema):
    start_date = fields.DateTime(required=False)
    start_organization_id = fields.Integer(required=True)
    destination_latitude = fields.Integer(required=True)
    destination_longitude = fields.Integer(required=True)
    max_destination_distance_km = fields.Integer(required=False)


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
    is_mine = fields.Boolean(required=True)


class OrganizationSchemaUserIDs(ma.ModelSchema):
    class Meta:
        model = Organization
        exclude = ['is_start_for']


class UserSchemaOrganizationInfo(ma.ModelSchema):
    class Meta:
        model = User
        include_fk = True
        exclude = ['password_hash', 'all_rides']
    is_driver = fields.Boolean()
    organizations = fields.Nested(OrganizationSchemaUserIDs, many=True)


class UserSchemaOrganizationIDs(ma.ModelSchema):
    class Meta:
        model = User
        include_fk = True
        exclude = ['password_hash', 'all_rides']
    is_driver = fields.Boolean()


class OrganizationSchemaUserInfo(ma.ModelSchema):
    class Meta:
        model = Organization
        exclude = ['is_start_for']
    users = fields.Nested(UserSchemaOrganizationIDs, many=True)


class PhotoURLSchema(ma.ModelSchema):
    photo_url = fields.String(required=True)

    @validates('photo_url')
    def check_photo_url(self, photo_url):
        return check_image_url(photo_url)


class OrganizationPhotoURLSchema(PhotoURLSchema):
    organization_id = fields.Integer(required=True)

    @validates('organization_id')
    def is_valid_organization(self, organization_id):
        organization = db.session.query(Organization).filter_by(id=organization_id).first()
        if not organization:
            raise ValidationError(f'Invalid organization with id: {organization_id}')
        return organization_id


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

    @validates('license_1')
    @validates('license_2')
    def is_valid_image_url(self, image_url):
        return check_image_url(image_url)


class RegisterUserSchema(ma.ModelSchema):
    class Meta:
        model = User
    email = fields.Email(required=True)
    password = fields.String(required=True)
    phone_number = fields.String(required=True)

    @validates('phone_number')
    def is_phone_like(self, phone_number):
        return check_phone_number(phone_number)

    @validates('email')
    def is_valid_email(self, email):
        return check_email(email)

    @validates('photo_url')
    def is_valid_avatar_url(self, avatar_url):
        return check_image_url(avatar_url)


class ChangePhoneSchema(ma.ModelSchema):
    phone_number = fields.String(required=True)

    @validates('phone_number')
    def is_phone_like(self, phone_number):
        return check_phone_number(phone_number)


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
        return check_email(email)


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


class ReverseGeocodingSchema(Schema):
    latitude = fields.Float(required=True)
    longitude = fields.Float(required=True)


class ForwardGeocodingSchema(Schema):
    address = fields.String(required=True)


class CarIdSchema(ma.ModelSchema):
    car_id = fields.Integer(required=True)
