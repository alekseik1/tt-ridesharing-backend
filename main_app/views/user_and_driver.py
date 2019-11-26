from flask import jsonify, request, abort
from flask_login import login_required, current_user
import phonenumbers

from app import db
from main_app.controller import validate_all, validate_params_with_schema, validate_is_in_db, \
    validate_is_authorized_with_id
from main_app.model import Driver, User, Car
from main_app.schemas import UserSchemaOrganizationInfo, RegisterDriverSchema, UserSchemaNoOrganizations, ChangePhoneSchema, \
    ChangeNameSchema, ChangeLastNameSchema, ChangeEmailSchema, PhotoURLSchema, CarSchema
from main_app.views import api
from main_app.responses import SwaggerResponses, build_error


@api.route('/get_user_info', methods=['GET'])
@login_required
def get_user_info():
    user_schema, car_schema = UserSchemaOrganizationInfo(), CarSchema(many=True)
    response = user_schema.dump(current_user)
    his_cars = db.session.query(Car).filter_by(owner_id=current_user.id).all()
    response['cars'] = car_schema.dump(his_cars)
    return jsonify(response), 200


@api.route('/am_i_driver', methods=['GET'])
@login_required
def am_i_driver():
    driver = db.session.query(Driver).filter_by(id=current_user.id).first()
    if driver:
        return jsonify(is_driver=True), 200
    return jsonify(is_driver=False)


def _get_user_info(user_id, include_organizations=True):
    if include_organizations:
        user_schema = UserSchemaOrganizationInfo()
    else:
        user_schema = UserSchemaNoOrganizations()
    user = db.session.query(User).filter_by(id=user_id).first()
    return user_schema.dump(user)


@api.route('/register_driver', methods=['POST'])
@login_required
def register_driver():
    data = request.get_json()
    user_id = data.get('id')
    schema = RegisterDriverSchema()
    errors = validate_all([
        validate_params_with_schema(schema, data=data),
        validate_is_in_db(db, user_id),
        validate_is_authorized_with_id(user_id, current_user),
    ])
    if errors:
        return errors
    driver = Driver(**schema.dump(data))
    db.session.add(driver)
    db.session.commit()
    return jsonify(user_id=driver.id), 200


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
