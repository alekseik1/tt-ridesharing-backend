from mimesis import Person
from model import User
from flask import jsonify
from utils.exceptions import ResponseExamples


def generate_random_person(locale='ru'):
    return Person(locale)


def validate_params_with_schema(schema, data):
    errors = schema.validate(data)
    if errors:
        error = ResponseExamples.some_params_are_invalid(list(errors.keys()))
        return jsonify(error), 400
    return None


def validate_is_in_db(db, user_id):
    user = db.session.query(User).filter_by(id=user_id).first()
    if user is None:
        error = ResponseExamples.INVALID_USER_WITH_ID
        error['value'] = user_id
        return jsonify(error), 400
    return None


def validate_is_authorized_with_id(id, current_user):
    if current_user.id != id:
        error = ResponseExamples.NO_PERMISSION_FOR_USER
        error['value'] = id
        return jsonify(error), 403
    return None


def validate_all(validation_results):
    for rv in validation_results:
        if rv:
            return rv
    return None
