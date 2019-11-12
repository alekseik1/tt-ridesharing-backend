from flask import jsonify, request
from flask_login import login_required, current_user

from app import db
from main_app.controller import validate_all, validate_params_with_schema, validate_is_in_db, \
    validate_is_authorized_with_id
from main_app.model import Driver, User
from main_app.schemas import UserSchema, RegisterDriverSchema, UserSchemaNoOrganizations
from main_app.views import api


@api.route('/get_user_info', methods=['GET'])
@login_required
def get_user_info():
    user_schema = UserSchema()
    response = user_schema.dump(current_user)
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
        user_schema = UserSchema()
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


@api.route('/get_multiple_users_info', methods=['POST'])
@login_required
def get_multiple_users_info():
    # TODO: more checks for bad data
    # TODO: Swagger documentation
    data = request.get_json().get('ids')
    if not data:
        return jsonify([])
    return jsonify([_get_user_info(user_id, include_organizations=False) for user_id in data])

