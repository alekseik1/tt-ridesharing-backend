from datetime import datetime

from flask import jsonify
from marshmallow import ValidationError
from email_validator import validate_email, EmailNotValidError
import phonenumbers

from main_app.model import User
from main_app.responses import SwaggerResponses


def validate_params_with_schema(schema, data):
    errors = schema.validate(data)
    if errors:
        error = SwaggerResponses.some_params_are_invalid(sorted(list(errors.keys())))
        return jsonify(error), 400
    return None


def validate_is_in_db(db, user_id):
    user = db.session.query(User).filter_by(id=user_id).first()
    if user is None:
        error = SwaggerResponses.INVALID_USER_WITH_ID
        error['value'] = user_id
        return jsonify(error), 400
    return None


def validate_is_authorized_with_id(id, current_user):
    if current_user.id != id:
        error = SwaggerResponses.NO_PERMISSION_FOR_USER
        error['value'] = id
        return jsonify(error), 403
    return None


def format_time(list_response):
    for x in list_response:
        dt = datetime.fromisoformat(x['start_time'])
        x['start_time'] = dt.strftime('%d %B %H:%M')
    return list_response


def validate_all(validation_results):
    for rv in validation_results:
        if rv:
            return rv
    return None


def check_email(email):
    from app import db
    try:
        email = validate_email(email)['email']
    except EmailNotValidError:
        raise ValidationError('Invalid email')
    user = db.session.query(User).filter_by(email=email).first()
    if user:
        raise ValidationError('Email is already registered')
    return email


def is_valid_phone_number(phone_number):
    try:
        validate_phone_number(phone_number)
    except ValidationError:
        return False
    return True


def validate_phone_number(phone_number):
    """
    Validates phone number via raising exceptions

    :param phone_number: String of number
    :return: A <Phone number> object from `phonenumbers` lib
    :raise: ValidationError
    """
    try:
        number = phonenumbers.parse(phone_number)
        if not phonenumbers.is_valid_number(number):
            raise ValidationError('Invalid phone number')
    except phonenumbers.NumberParseException:
        raise ValidationError('Invalid phone number')
    return phone_number


def format_phone_number(phone_number_str):
    number = phonenumbers.parse(phone_number_str)
    return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)


def check_phone_number(phone_number):
    return format_phone_number(validate_phone_number(phone_number))


def check_image_url(photo_url):
    # TODO: validate if photo url is in our S3 storage
    return photo_url
