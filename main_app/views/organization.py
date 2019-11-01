from flask import request, jsonify
from flask_login import login_required, current_user

from app import db
from main_app.model import Organization
from main_app.schemas import OrganizationIDSchema, UserSchema, OrganizationSchema
from main_app.views import api, MAX_ORGANIZATIONS_PER_USER
from main_app.responses import SwaggerResponses
from main_app.controller import validate_params_with_schema, validate_all


@api.route('/leave_organization', methods=['POST'])
@login_required
def leave_organization():
    """
    {'organization_id': 36}

    :return:
    """
    data = request.get_json()
    errors = validate_all([validate_params_with_schema(OrganizationIDSchema(), data)])
    if errors:
        return errors
    organization_id = data['organization_id']
    organization_to_leave = db.session.query(Organization).filter_by(id=organization_id).first()
    if not organization_to_leave:
        error = SwaggerResponses.INVALID_ORGANIZATION_ID
        error['value'] = organization_id
        return jsonify(organization_id), 400
    if organization_to_leave not in current_user.organizations:
        error = SwaggerResponses.ERROR_NOT_IN_ORGANIZATION
        error['value'] = organization_id
        return jsonify(error), 400
    current_user.organizations.remove(organization_to_leave)
    db.session.commit()
    response = SwaggerResponses.ORGANIZATION_ID
    response['value'] = organization_id
    return jsonify(response), 200


@api.route('/join_organization', methods=['POST'])
@login_required
def join_organization():
    """
    {'organization_id": 34}

    :return:
    """
    data = request.get_json()
    errors = validate_all([validate_params_with_schema(OrganizationIDSchema(), data)])
    if errors:
        return errors
    if len(current_user.organizations) >= MAX_ORGANIZATIONS_PER_USER:
        error = SwaggerResponses.ORGANIZATION_LIMIT
        return jsonify(error), 400
    data_organization_id = data['organization_id']
    organization = db.session.query(Organization).filter_by(id=data_organization_id).first()
    if not organization:
        error = SwaggerResponses.INVALID_ORGANIZATION_ID
        error['value'] = data_organization_id
        return jsonify(error), 400
    current_user.organizations.append(organization)
    db.session.commit()
    # TODO: сделать его
    response = SwaggerResponses.ORGANIZATION_ID
    response['organization_id'] = organization.id
    return jsonify(response), 200


@api.route('/get_my_organization_members', methods=['GET'])
@login_required
def get_my_organization_members():
    data = request.args
    user_schema = UserSchema(many=True)
    id = data.get('organization_id')
    try:
        id = int(id)
    except:
        error = SwaggerResponses.INVALID_ORGANIZATION_ID
        error['value'] = id
        return jsonify(error), 400
    organization = db.session.query(Organization).filter_by(id=id).first()
    if organization not in current_user.organizations:
        error = SwaggerResponses.NO_PERMISSION_FOR_USER
        error['value'] = current_user.id
        return jsonify(error), 403
    response = user_schema.dump(organization.users)
    return jsonify(response), 200


@api.route('/get_all_organizations', methods=['GET'])
@login_required
def get_all_organizations():
    organization_schema = OrganizationSchema(many=True)
    result = organization_schema.dump(db.session.query(Organization).all(), many=True)
    return jsonify(result), 200