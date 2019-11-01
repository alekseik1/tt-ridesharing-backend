from flask import jsonify, request
from flask_login import current_user, logout_user, login_user
from sqlalchemy.exc import IntegrityError

from app import db
from main_app.model import User
from main_app.schemas import RegisterUserSchema
from main_app.views import api
from utils.exceptions import ResponseExamples
from utils.misc import validate_all, validate_params_with_schema


@api.route('/logout', methods=['POST'])
def logout():
    # Check if current user is authenticated
    if not current_user.is_authenticated:
        error = ResponseExamples.AUTHORIZATION_REQUIRED
        return jsonify(error), 400
    logout_user()
    return '', 200


@api.route('/login', methods=['POST'])
def login():
    # Check if current user is authenticated
    if current_user.is_authenticated:
        error = ResponseExamples.ALREADY_LOGGED_IN
        return jsonify(error), 400
    data = request.get_json()
    login = data.get('login')
    password = data.get('password')
    # We login only via email for now
    user = User.query.filter_by(email=login).first()
    if user is None or not user.check_password(password):
        error = ResponseExamples.INCORRECT_LOGIN
        return jsonify(error), 400
    login_user(user, remember=True)
    response = ResponseExamples.USER_ID
    response['user_id'] = user.id
    return jsonify(response), 200


@api.route('/register_user', methods=['POST'])
def register_user():
    data = request.get_json()
    errors = validate_all([validate_params_with_schema(RegisterUserSchema(), data)])
    if errors:
        return errors
    user = User(first_name=data['first_name'], last_name=data['last_name'], email=data['email'])
    user.set_password(password=data['password'])
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError as e:
        error = ResponseExamples.EMAIL_IS_BUSY
        error['value'] = data['email']
        return jsonify(error), 400
    return jsonify(user_id=user.id)