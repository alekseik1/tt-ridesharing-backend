from marshmallow import fields, validates, Schema, post_load
from marshmallow.validate import Length

from app import ma, db
from main_app.model import Ride, User, Organization, Car, JoinRideRequest
from settings import MAX_EMAIL_LENGTH
from main_app.controller import parse_phone_number


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


class JoinRideJsonSchema(ma.ModelSchema, CamelCaseSchema):
    class Meta:
        model = JoinRideRequest
        sqla_session = db.session
        include_fk = True


class RideJsonSchema(ma.ModelSchema, CamelCaseSchema):
    class Meta:
        model = Ride
        sqla_session = db.session
    stop_address = fields.String(dump_only=True)
    free_seats = fields.Integer(dump_only=True)
    car = fields.Nested('CarSchema')
    car_id = fields.Integer(required=True, load_only=True)
    start_organization = fields.Nested('OrganizationJsonSchema')
    start_organization_id = fields.Integer(required=True, load_only=True)
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
    start_organization_address = fields.Function(
        lambda obj: obj.start_organization.address, dump_only=True)
    start_organization_name = fields.Function(
        lambda obj: obj.start_organization.name, dump_only=True)
    fields.Function()


class IdSchema(CamelCaseSchema):
    id = fields.Integer(required=True)


class UserJsonSchema(ma.ModelSchema, CamelCaseSchema):
    class Meta:
        model = User
    organizations = fields.Nested('OrganizationJsonSchema', many=True)
    rating = fields.Float(dump_only=True)


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
    latitude = fields.Float(load_only=True)
    longitude = fields.Float(load_only=True)

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


class UserIDSchema(Schema):
    id = fields.Integer(data_key='user_id', required=True)


class RegisterUserSchema(ma.ModelSchema):
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
        user_obj.phone_number = parse_phone_number(data['phone_number'])
        return user_obj


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


class RideSearchSchema(Schema):
    id = fields.Integer(data_key='organization_id', required=True)
    latitude = fields.Float(required=True)
    longitude = fields.Float(required=True)


class ReverseGeocodingSchema(Schema):
    latitude = fields.Float(required=True)
    longitude = fields.Float(required=True)


class ForwardGeocodingSchema(Schema):
    address = fields.String(required=True)
