from marshmallow import fields, validates, ValidationError, Schema, post_load
from marshmallow.validate import Length, OneOf
from flask import jsonify

from app import ma, db
from main_app.model import Ride, User, Organization, Car, JoinRideRequest, RideFeedback
from settings import MAX_EMAIL_LENGTH
from main_app.controller import check_email, parse_phone_number, check_image_url
from main_app.responses import SwaggerResponses

STANDART_RIDE_INFO = [
    'id', 'free_seats',
    'submit_datetime', 'host',
    'price', 'car', 'address', 'from_organization',
    'host_answer', 'decline_reason', 'organization', 'start_datetime'
]


def camelcase(s):
    parts = iter(s.split("_"))
    return next(parts) + "".join(i.title() for i in parts)


class CamelCaseSchema(Schema):
    """Schema that uses camel-case for its external representation
    and snake-case for its internal representation.
    """

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class LoginSchema(Schema):
    login = fields.Email(required=True, validate=Length(max=MAX_EMAIL_LENGTH))
    password = fields.String(required=True)


# OLD CODE #


class FindBestRidesSchema(ma.ModelSchema):
    start_date = fields.DateTime(required=False)
    organization_id = fields.Integer(required=True)
    latitude = fields.Integer(required=True)
    longitude = fields.Integer(required=True)
    from_organization = fields.Boolean(required=True)
    max_destination_distance_km = fields.Integer(required=False)


class OrganizationIDSchema(ma.ModelSchema):
    organization_id = fields.Integer(required=True)


class CreateRideSchema(ma.ModelSchema):
    organization_id = fields.Integer(required=True)
    latitude = fields.Float(required=True)
    longitude = fields.Float(required=True)
    address = fields.String(required=False)
    start_time = fields.String(required=True)
    description = fields.String(required=False)
    total_seats = fields.Integer(required=True)
    cost = fields.Float(required=False)
    # TODO: rewrite as Nested(Car(only=('id', )))
    car_id = fields.Integer(required=True)
    from_organization = fields.Boolean(required=True)

    @validates('start_time')
    def is_not_empty(self, value):
        if len(value) == 0:
            raise ValidationError('Should not be empty string')

    @validates('car_id')
    def car_exists(self, car_id):
        car = db.session.query(Car).filter_by(id=car_id).first()
        if not car:
            raise ValidationError('Invalid car')


class JoinRideJsonSchema(ma.ModelSchema, CamelCaseSchema):
    class Meta:
        model = JoinRideRequest
        sqla_session = db.session
        include_fk = True
    user = fields.Nested('UserJsonSchema', only=(
        'id', 'first_name', 'last_name', 'photo_url', 'rating'
    ))


class RideSchema(ma.ModelSchema):
    class Meta:
        model = Ride
        include_fk = True
    is_mine = fields.Boolean(required=True)


class RideJsonSchema(ma.ModelSchema, CamelCaseSchema):
    class Meta:
        model = Ride
        sqla_session = db.session
    address = fields.String(dump_only=True)
    free_seats = fields.Integer(dump_only=True)
    car = fields.Nested('CarSchema')
    car_id = fields.Integer(required=True, load_only=True)
    organization = fields.Nested('OrganizationJsonSchema', only=(
        'id', 'name', 'address',
    ))
    organization_id = fields.Integer(required=True, load_only=True)
    rating = fields.Integer(required=False, dump_only=True)
    total_seats = fields.Integer(required=True)
    price = fields.Float(required=True)
    host = fields.Nested('UserJsonSchema', only=(
        'id', 'first_name', 'last_name', 'photo_url', 'rating', 'phone_number'
    ))
    host_answer = fields.String(dump_only=True)
    decline_reason = fields.String(dump_only=True)
    passengers = fields.Nested('UserJsonSchema', many=True, only=(
        'id', 'first_name', 'last_name', 'photo_url', 'rating',
    ))
    organization_address = fields.Function(
        lambda obj: obj.organization.address, dump_only=True)
    organization_name = fields.Function(
        lambda obj: obj.organization.name, dump_only=True)
    join_requests = fields.Nested(JoinRideJsonSchema, many=True, only=(
        'ride_id', 'user', 'status', 'decline_reason'
    ))


class OrganizationSchemaUserIDs(ma.ModelSchema):
    class Meta:
        model = Organization
        exclude = ['rides']


class UserSchemaOrganizationInfo(ma.ModelSchema):
    class Meta:
        model = User
        include_fk = True
        exclude = ['_password_hash', 'all_rides']
    is_driver = fields.Boolean()
    organizations = fields.Nested(OrganizationSchemaUserIDs, many=True)


class IdSchema(CamelCaseSchema):
    id = fields.Integer(required=True)


class UserJsonSchema(ma.ModelSchema, CamelCaseSchema):
    class Meta:
        model = User
        sqla_session = db.session
    organizations = fields.Nested('OrganizationJsonSchema', many=True)
    rating = fields.Float(dump_only=True)


class UserChangeSchema(CamelCaseSchema):
    first_name = fields.String(required=False)
    last_name = fields.String(required=False)
    email = fields.String(required=False)
    phone_number = fields.String(required=False)
    about = fields.String(required=False)


class JoinOrganizationSchema(CamelCaseSchema):
    id = fields.Integer(required=True)
    control_answer = fields.String(required=True)


class OrganizationJsonSchema(ma.ModelSchema, CamelCaseSchema):
    class Meta:
        model = Organization
        sqla_session = db.session
    last_ride_datetime = fields.String(dump_only=True)
    users = fields.Nested(UserJsonSchema, only=(
        'id', 'first_name', 'last_name', 'photo_url', 'rating'
    ), many=True, data_key='members')
    total_members = fields.String(dump_only=True)
    total_drivers = fields.String(dump_only=True)
    min_ride_cost = fields.String(dump_only=True)
    max_ride_cost = fields.String(dump_only=True)
    # Not for dumping
    control_question = fields.String()
    control_answer = fields.String(load_only=True)
    latitude = fields.Float(required=True)
    longitude = fields.Float(required=True)

    creator = fields.Nested(UserJsonSchema, data_key='creator', dump_only=True, only=[
        'id', 'photo_url'
    ])


class OrganizationPermissiveSchema(OrganizationJsonSchema):
    __required__ = ('id', )

    class Meta:
        model = Organization
        sqla_session = db.session
        only = ('id', 'name', 'latitude', 'longitude')

    def on_bind_field(self, field_name, field_obj):
        super().on_bind_field(field_name, field_obj)
        # Mark all fields as `required=False`
        if field_name not in self.__required__:
            field_obj.required = False


class UserSchemaOrganizationIDs(ma.ModelSchema):
    class Meta:
        model = User
        include_fk = True
        exclude = ['_password_hash', 'all_rides']
    is_driver = fields.Boolean()


class OrganizationSchemaUserInfo(ma.ModelSchema):
    class Meta:
        model = Organization
        exclude = ['rides']
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
        exclude = ['_password_hash', 'all_rides']


class UserIDSchema(Schema):
    id = fields.Integer(data_key='user_id', required=True)


class RegisterUserSchema(ma.ModelSchema, CamelCaseSchema):
    class Meta:
        model = User
        exclude = ['_password_hash', 'id', ]
    email = fields.Email(required=True)
    password = fields.String(required=True)
    phone_number = fields.String(required=True)

    @validates('phone_number')
    def is_phone_like(self, phone_number):
        return parse_phone_number(phone_number)

    @validates('photo_url')
    def is_valid_avatar_url(self, avatar_url):
        pass

    @post_load(pass_original=True)
    def make_user(self, user_obj: User, data, **kwargs):
        user_obj.password = data['password']
        user_obj.phone_number = parse_phone_number(data['phoneNumber'])
        return user_obj


class ChangePhoneSchema(ma.ModelSchema):
    phone_number = fields.String(required=True)

    @validates('phone_number')
    def is_phone_like(self, phone_number):
        return parse_phone_number(phone_number)


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


class CarSchema(ma.ModelSchema, CamelCaseSchema):
    class Meta:
        model = Car
        sqla_session = db.session
    id = fields.Integer(required=True)


class CarPermissiveSchema(CarSchema):
    __required__ = ('id', )

    def on_bind_field(self, field_name, field_obj):
        super().on_bind_field(field_name, field_obj)
        # Mark all fields as `required=False`
        if field_name not in self.__required__:
            field_obj.required = False


class RegisterCarForDriverSchema(ma.ModelSchema):
    class Meta:
        model = Car
    # Leave this field only for validation
    owner_id = fields.Integer(required=False)

    @validates('owner_id')
    def owner_exists(self, owner_id):
        if db.session.query(User).filter_by(id=owner_id).first() is None:
            error = SwaggerResponses.INVALID_DRIVER_WITH_ID
            error['value'] = owner_id
            return jsonify(error), 400


class RideSearchSchema(CamelCaseSchema):
    id = fields.Integer(data_key='organization_id', required=True)
    latitude = fields.Float(required=True)
    longitude = fields.Float(required=True)
    from_organization = fields.Boolean(required=True)


class ReverseGeocodingSchema(Schema):
    latitude = fields.Float(required=True)
    longitude = fields.Float(required=True)


class ForwardGeocodingSchema(Schema):
    address = fields.String(required=True)


class CarIdSchema(ma.ModelSchema):
    car_id = fields.Integer(required=True)


class RideFeedbackSchema(ma.ModelSchema, CamelCaseSchema):
    class Meta:
        model = RideFeedback
        sqla_session = db.session
    ride = fields.Nested(RideJsonSchema, only=('id', ), required=True)


class SearchSchema(CamelCaseSchema):
    query = fields.String(required=True)


class PasswordChangeSchema(CamelCaseSchema):
    old_password = fields.String(required=True)
    new_password = fields.String(required=True)


class UploadFileSchema(CamelCaseSchema):
    file_type = fields.String(required=True)

    @validates('file_type')
    def is_image(self, file_type):
        if file_type not in ['png', 'jpeg']:
            raise ValidationError('File type should be `png` or `jpeg`')


class UpdateFirebaseIdSchema(CamelCaseSchema):
    token = fields.String(required=True)


class SubscribeToDriverSchema(CamelCaseSchema):
    id = fields.Integer(required=True)
    action = fields.String(validate=OneOf(['SUBSCRIBE', 'UNSUBSCRIBE']), required=True)
