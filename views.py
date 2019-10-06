from flask import request, jsonify, url_for, redirect, flash
from flask_login import current_user, login_user
from model import UserSchema, User
from utils.exceptions import InvalidData
from flask import current_app as app


@app.route('/')
def root():
    return redirect(url_for(index.__name__))


@app.route('/index')
def index():
    return 'Welcome to our service!'


@app.route('/api/register_user', methods=['GET', 'POST'])
def register_user():
    user_schema = UserSchema()
    errors = user_schema.validate(request.form)
    for column, error in errors.items():
        raise InvalidData(f'Error at `{column}` -- {error[0]}')
    return 'Not implemented'


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for(index.__name__))
    email = request.values.get('email')
    password = request.values.get('password')
    user = User.query.filter_by(email=email).first()
    if user is None or not user.check_password(password):
        flash('Invalid email or password')
        return redirect(url_for(login.__name__))
    login_user(user, remember=True)
    return redirect(url_for(index.__name__))


@app.errorhandler(InvalidData)
def handle_invalid_data_error(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response
