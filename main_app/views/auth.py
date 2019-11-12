from flask import jsonify, request
from flask_login import current_user, logout_user, login_user
from sqlalchemy.exc import IntegrityError

from app import db
from main_app.model import User
from main_app.schemas import RegisterUserSchema
from main_app.views import api
from main_app.responses import SwaggerResponses, build_error
from main_app.controller import validate_params_with_schema, validate_all


@api.route('/logout', methods=['POST'])
def logout():
    # Check if current user is authenticated
    if not current_user.is_authenticated:
        error = build_error(SwaggerResponses.AUTHORIZATION_REQUIRED)
        return jsonify(error), 400
    logout_user()
    return '', 200


@api.route('/login', methods=['POST'])
def login():
    # Check if current user is authenticated
    if current_user.is_authenticated:
        error = build_error(SwaggerResponses.ALREADY_LOGGED_IN)
        return jsonify(error), 400
    data = request.get_json()
    login = data.get('login')
    password = data.get('password')
    # We login only via email for now
    user = User.query.filter_by(email=login).first()
    if user is None or not user.check_password(password):
        error = build_error(SwaggerResponses.INCORRECT_LOGIN)
        return jsonify(error), 400
    login_user(user, remember=True)
    response = SwaggerResponses.USER_ID
    response['user_id'] = user.id
    return jsonify(response), 200


@api.route('/register_user', methods=['POST'])
def register_user():
    data = request.get_json()
    errors = validate_all([validate_params_with_schema(RegisterUserSchema(), data)])
    if errors:
        return errors
    user = User(
        first_name=data['first_name'],
        last_name=data['last_name'],
        email=data['email'],
        phone_number=data['phone_number']
    )
    user.set_password(password=data['password'])
    db.session.add(user)
    db.session.commit()
    return jsonify(user_id=user.id)


@api.route('/get_auth', methods=['GET'])
def get_auth():
    if not current_user.is_authenticated:
        return jsonify(dict(is_valid=False))
    else:
        return jsonify(dict(is_valid=True, user_id=current_user.id))
