from flask import jsonify, request
from flask_login import login_required, current_user

from main_app.schemas import OrganizationJsonSchema, UserJsonSchema
from main_app.exceptions.custom import InsufficientPermissions
from main_app.views import api


@api.route('/user/organizations', methods=['GET'])
@login_required
def organizations():
    return jsonify(OrganizationJsonSchema(only=('id', 'name', 'address'), many=True).dump(
        current_user.organizations
    ))


@api.route('/user', methods=['GET'])
@login_required
def user():
    user = UserJsonSchema(only=('id', )).load(request.args)
    if user.id is None:
        user = current_user
    if user.email is None:
        raise InsufficientPermissions()
    return UserJsonSchema(
        only=('id', 'first_name', 'last_name', 'rating', 'photo_url')
    ).dump(user)
