from marshmallow import ValidationError
from flask import jsonify


def handle_validation_error(e: ValidationError):
    response = {
        'code': 400,
        'name': 'Some of required fields are invalid',
        'value': e.messages,
    }
    return jsonify(response), 400
