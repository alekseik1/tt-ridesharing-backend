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


@api.route('/api/register_user', methods=['GET', 'POST'])
def register_user():
    user_schema = RegisterUserSchema()
    errors = user_schema.validate(request.json)
    for column, error in errors.items():
        raise InvalidData(f'Error at `{column}` -- {error[0]}')
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


@api.route('/api/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('.'+index.__name__))
    email = request.values.get('email')
    password = request.values.get('password')
    user = User.query.filter_by(email=email).first()
    if user is None or not user.check_password(password):
        flash('Invalid email or password')
        # BUG: we infinitely redirect to the same page
        return redirect(url_for('.'+login.__name__))
    login_user(user, remember=True)
    return redirect(url_for('.'+index.__name__))
