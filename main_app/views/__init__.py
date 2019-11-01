from flask import Blueprint, redirect, url_for

api = Blueprint('api', __name__)
# TODO: перенести это в конфиг
MAX_ORGANIZATIONS_PER_USER = 5


@api.route('/', methods=['GET', 'POST'])
def root():
    return redirect(url_for('.'+index.__name__))


@api.route('/index')
def index():
    return 'Welcome to our service!'
