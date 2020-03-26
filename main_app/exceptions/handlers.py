from marshmallow import ValidationError
from werkzeug.exceptions import HTTPException, Unauthorized, Forbidden
from flask import jsonify, current_app


def handle_validation_error(e: ValidationError):
    response = {
        'code': 400,
        'description': e.messages,
    }
    return jsonify(response), 400


def handle_uncaught_error(error):
    """
    Last gateway for errors. Does not rely on `error` attributes

    :param error: exception instance. Will be dumped to logs
    :return:
    """
    current_app.logger.error(error)
    return jsonify({
        'code': 500,
        'description': 'Uncaught error',
    }), 500


GENERIC_EXCEPTIONS = {
    Unauthorized, HTTPException, Forbidden,
}
SPECIAL_EXCEPTIONS = {
    ValidationError: handle_validation_error,
    # Exception: handle_uncaught_error
}


def handler_factory(error_class: HTTPException):
    def handler(e: error_class):
        response = {
            'code': e.code,
            'description': e.description,
        }
        return jsonify(response), e.code
    return handler


def setup_handlers(app):
    # Exceptions that are all the same
    for exception in GENERIC_EXCEPTIONS:
        app.register_error_handler(exception, handler_factory(exception))
    # Exceptions that require extra logic (e.g. logging)
    for exception, handler in SPECIAL_EXCEPTIONS.items():
        app.register_error_handler(exception, handler)
