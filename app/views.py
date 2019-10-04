from app import app
from flask import request, abort, jsonify
from model import UserSchema
from utils.exceptions import InvalidData


@app.route('/')
@app.route('/<string:name>')
def index(name='world'):
    return f'Hello, {name}'


@app.route('/api/register_user', methods=['GET', 'POST'])
def register_user():
    user_schema = UserSchema()
    errors = user_schema.validate(request.form)
    for column, error in errors.items():
        raise InvalidData(f'Error at `{column}` -- {error[0]}')
    return 'Not implemented'


@app.errorhandler(InvalidData)
def handle_invalid_data_error(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response
