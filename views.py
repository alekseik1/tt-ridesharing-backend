from flask import request, url_for, redirect, flash, Blueprint, jsonify
from flask_login import current_user, login_user
from model import RegisterUserSchema, User
from sqlalchemy.exc import IntegrityError
from utils.exceptions import InvalidData, ResponseExamples
from app import db

api = Blueprint('api', __name__)


@api.route('/', methods=['GET', 'POST'])
def root():
    return redirect(url_for('.'+index.__name__))


@api.route('/index')
def index():
    return 'Welcome to our service!'


@api.route('/register_user', methods=['GET', 'POST'])
def register_user():
    user_schema = RegisterUserSchema()
    errors = user_schema.validate(request.json)
    if errors:
        error = ResponseExamples.some_params_are_invalid(list(errors.keys()))
        return jsonify(error), 400
    data = request.get_json()
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


@api.route('/login', methods=['GET', 'POST'])
def login():
    # Check if current user is authenticated
    if current_user.is_authenticated:
        error = ResponseExamples.ALREADY_LOGGED_IN
        return error, 400
    data = request.get_json()
    login = data.get('login')
    password = data.get('password')
    # We login only via email for now
    user = User.query.filter_by(email=login).first()
    if user is None or not user.check_password(password):
        error = ResponseExamples.INCORRECT_LOGIN
        return error, 400
    login_user(user, remember=True)
    response = ResponseExamples.USER_ID
    response['user_id'] = user.id
    return response, 200
