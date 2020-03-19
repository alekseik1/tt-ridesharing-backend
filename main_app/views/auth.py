from flask import jsonify, request
from flask_login import current_user, logout_user, login_user
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from app import db
from main_app.model import User
from main_app.schemas import RegisterUserSchema, LoginSchema, UserIDSchema
from main_app.views import api
from main_app.responses import SwaggerResponses, build_error
from main_app.controller import parse_phone_number
from main_app.exceptions import InvalidCredentials, AlreadyLoggedIn, EmailBusy


@api.route('/logout', methods=['POST'])
def logout():
    # Check if current user is authenticated
    if not current_user.is_authenticated:
        error = build_error(SwaggerResponses.AUTHORIZATION_REQUIRED)
        return jsonify(error), 400
    logout_user()
    return ''


@api.route('/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        raise AlreadyLoggedIn()
    data = LoginSchema().load(request.json)
    login, password = data['login'], data['password']
    try:
        user = User.query.filter_by(phone_number=parse_phone_number(login)).first()
    except ValidationError:
        user = User.query.filter_by(email=login).first()
    if user is None or not user.check_password(password):
        raise InvalidCredentials()
    login_user(user, remember=True)
    return UserIDSchema().dump(user)


@api.route('/register_user', methods=['POST'])
def register_user():
    user = RegisterUserSchema().load(request.json, session=db.session)
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise EmailBusy()
    return UserIDSchema().dump(user)


@api.route('/get_auth', methods=['GET'])
def get_auth():
    if not current_user.is_authenticated:
        return jsonify({'is_valid': False})
    else:
        return jsonify({'is_valid': True, 'user_id': current_user.id})
