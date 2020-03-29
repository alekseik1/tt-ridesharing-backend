from flask import jsonify, request
from flask_login import login_required, current_user
import phonenumbers

from app import db
from main_app.controller import validate_params_with_schema
from main_app.model import User, Car
from main_app.schemas import UserSchemaOrganizationInfo,\
    UserSchemaNoOrganizations, ChangePhoneSchema, \
    ChangeNameSchema, ChangeLastNameSchema, ChangeEmailSchema,\
    PhotoURLSchema, CarSchema, OrganizationJsonSchema, UserJsonSchema
from main_app.exceptions.custom import InsufficientPermissions
from main_app.views import api


@api.route('/user/organizations', methods=['GET'])
@login_required
def organizations():
    return jsonify(OrganizationJsonSchema(only=('id', 'name', 'address'), many=True).dump(
        current_user.organizations
    ))


@api.route('/user', methods=['GET'])
@login_required
def user():
    user = UserJsonSchema(only=('id', )).load(request.args)
    if user.email is None:
        raise InsufficientPermissions()
    return UserJsonSchema(
        only=('first_name', 'last_name', 'rating', 'photo_url')
    ).dump(user)


@api.route('/get_user_info', methods=['GET'])
@login_required
def get_user_info():
    user_schema, car_schema = UserSchemaOrganizationInfo(), CarSchema(many=True)
    response = user_schema.dump(current_user)
    his_cars = db.session.query(Car).filter_by(owner_id=current_user.id).all()
    response['cars'] = car_schema.dump(his_cars)
    return jsonify(response), 200


def _get_user_info(user_id, include_organizations=True):
    if include_organizations:
        user_schema = UserSchemaOrganizationInfo()
    else:
        user_schema = UserSchemaNoOrganizations()
    user = db.session.query(User).filter_by(id=user_id).first()
    return user_schema.dump(user)


@api.route('/change_phone_number', methods=['POST', 'PATCH'])
def change_number():
    data = request.get_json()
    errors = validate_params_with_schema(ChangePhoneSchema(), data)
    if errors:
        return errors
    new_number = phonenumbers.format_number(
        phonenumbers.parse(data.get('phone_number')),
        phonenumbers.PhoneNumberFormat.E164
    )
    current_user.phone_number = new_number
    db.session.commit()
    return get_user_info()


@api.route('/get_multiple_users_info', methods=['POST'])
@login_required
def get_multiple_users_info():
    # TODO: more checks for bad data
    # TODO: Swagger documentation
    data = request.get_json().get('ids')
    if not data:
        return jsonify([])
    return jsonify([_get_user_info(user_id, include_organizations=False) for user_id in data])


@api.route('/change_first_name', methods=['PATCH', 'POST'])
@login_required
def change_first_name():
    data = request.get_json()
    name = data.get('first_name')
    errors = validate_params_with_schema(ChangeNameSchema(), data)
    if errors:
        return errors
    current_user.first_name = name
    db.session.commit()
    return get_user_info()


@api.route('/change_last_name', methods=['PATCH', 'POST'])
@login_required
def change_last_name():
    data = request.get_json()
    name = data.get('last_name')
    errors = validate_params_with_schema(ChangeLastNameSchema(), data)
    if errors:
        return errors
    current_user.last_name = name
    db.session.commit()
    return get_user_info()


@api.route('/change_email', methods=['PATCH', 'POST'])
@login_required
def change_email():
    data = request.get_json()
    email = data.get('email')
    errors = validate_params_with_schema(ChangeEmailSchema(), data)
    if errors:
        return errors
    current_user.email = email
    db.session.commit()
    return get_user_info()


@api.route('/upload_avatar', methods=['POST'])
@login_required
def upload_avatar():
    data = request.get_json()
    photo_url = data.get('photo_url')
    errors = validate_params_with_schema(PhotoURLSchema(), data)
    if errors:
        return errors
    current_user.photo_url = photo_url
    db.session.commit()
    return get_user_info()
