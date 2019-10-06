from flask import request, url_for, redirect, flash, Blueprint
from flask_login import current_user, login_user
from model import UserSchema, User
from utils.exceptions import InvalidData


root_page = Blueprint('root', __name__)
@root_page.route('/')
def root():
    return redirect(url_for('{0}.{0}'.format(index.__name__)))


index_page = Blueprint('index', __name__)
@index_page.route('/index')
def index():
    return 'Welcome to our service!'


register_page = Blueprint('register_user', __name__)
@register_page.route('/api/register_user', methods=['GET', 'POST'])
def register_user():
    user_schema = UserSchema()
    errors = user_schema.validate(request.form)
    for column, error in errors.items():
        raise InvalidData(f'Error at `{column}` -- {error[0]}')
    return 'Not implemented'


login_page = Blueprint('login', __name__)
@login_page.route('/api/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('{0}.{0}'.format(index.__name__)))
    email = request.values.get('email')
    password = request.values.get('password')
    user = User.query.filter_by(email=email).first()
    if user is None or not user.check_password(password):
        flash('Invalid email or password')
        # BUG: we infinitely redirect to the same page
        return redirect(url_for('{0}.{0}'.format(login.__name__)))
    login_user(user, remember=True)
    return redirect(url_for('{0}.{0}'.format(index.__name__)))
