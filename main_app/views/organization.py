from flask import request, jsonify
from flask_login import login_required, current_user
from werkzeug.exceptions import Forbidden

from app import db
from main_app.model import Organization
from main_app.schemas import OrganizationIDSchema, UserSchemaOrganizationInfo, \
    OrganizationSchemaUserIDs, OrganizationSchemaUserInfo, OrganizationPhotoURLSchema, \
    IdSchema, OrganizationJsonSchema, JoinOrganizationSchema
from main_app.exceptions.custom import IncorrectControlAnswer
from main_app.views import api, MAX_ORGANIZATIONS_PER_USER
from main_app.model import User
from main_app.misc import reverse_geocoding_blocking
from main_app.responses import SwaggerResponses, build_error
from main_app.controller import validate_params_with_schema, validate_all


@api.route('/organization', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def organization():
    if request.method == 'GET':
        return OrganizationJsonSchema(exclude=('users', 'is_start_for', 'control_question')).dump(
            db.session.query(Organization).filter_by(
                **IdSchema().load(request.args)
            ).first()
        )
    if request.method == 'PUT':
        org = OrganizationJsonSchema().load(request.json)
        org.creator = current_user
        org.address = reverse_geocoding_blocking(
            latitude=org.latitude, longitude=org.longitude
        )['address']
        db.session.add(org)
        db.session.commit()
        return IdSchema().dump(org)
    if request.method == 'POST':
        # BUG: может быть больше параметров, и он съет
        # Надо написать отдельную схему на PUT и POST
        org = OrganizationJsonSchema().load(request.json)
        if current_user != org.creator:
            raise Forbidden('Only creator can edit organization info')
        db.session.add(org)
        db.session.commit()
        return IdSchema().dump(org)
    if request.method == 'DELETE':
        org = OrganizationJsonSchema(only=('id', )).load(request.json)
        if current_user != org.creator:
            raise Forbidden('Only creator can delete an organization')
        db.session.delete(org)
        db.session.commit()
        return ''


@api.route('/organization/members', methods=['GET'])
@login_required
def organization_members():
    return OrganizationJsonSchema(only=('id', 'users')).dump(
        db.session.query(Organization).filter_by(**IdSchema().load(request.args)).first()
    )


@api.route('/organization/question', methods=['GET'])
def question():
    return OrganizationJsonSchema(only=('id', 'control_question')).dump(
        db.session.query(Organization).filter_by(**IdSchema().load(request.args)).first()
    )


@api.route('/organization/join', methods=['POST'])
def join():
    data = JoinOrganizationSchema().load(request.json)
    org = db.session.query(Organization).filter_by(id=data['id']).first()
    if org.control_answer != data['control_answer']:
        raise IncorrectControlAnswer()
    if current_user not in org.users:
        org.users.append(current_user)
        db.session.commit()
    return IdSchema().dump(org)


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
        error = build_error(SwaggerResponses.INVALID_ORGANIZATION_ID, organization_id)
        return jsonify(error), 400
    if organization_to_leave not in current_user.organizations:
        error = build_error(SwaggerResponses.ERROR_NOT_IN_ORGANIZATION, organization_id)
        return jsonify(error), 400
    current_user.organizations.remove(organization_to_leave)
    db.session.commit()
    response = SwaggerResponses.ORGANIZATION_ID
    response['organization_id'] = organization_id
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
        error = build_error(SwaggerResponses.ORGANIZATION_LIMIT)
        return jsonify(error), 400
    data_organization_id = data['organization_id']
    organization = db.session.query(Organization).filter_by(id=data_organization_id).first()
    if not organization:
        error = build_error(SwaggerResponses.INVALID_ORGANIZATION_ID, data_organization_id)
        return jsonify(error), 400
    if organization in current_user.organizations:
        error = build_error(SwaggerResponses.INVALID_ORGANIZATION_ID, data_organization_id)
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
    user_schema = UserSchemaOrganizationInfo(many=True)
    id = data.get('organization_id')
    try:
        id = int(id)
    except ValueError:
        error = build_error(SwaggerResponses.INVALID_ORGANIZATION_ID, id)
        return jsonify(error), 400
    organization = db.session.query(Organization).filter_by(id=id).first()
    if organization not in current_user.organizations:
        error = build_error(SwaggerResponses.NO_PERMISSION_FOR_USER, current_user.id)
        return jsonify(error), 403
    response = user_schema.dump(organization.users)
    return jsonify(response), 200


@api.route('/get_all_organizations', methods=['GET'])
@login_required
def get_all_organizations():
    organization_schema = OrganizationSchemaUserInfo(many=True)
    result = organization_schema.dump(db.session.query(Organization).all(), many=True)
    return jsonify(result), 200


@api.route('/create_organization', methods=['POST'])
@login_required
def create_organization():
    organization_schema = OrganizationSchemaUserIDs()
    data = request.get_json()
    errors = validate_params_with_schema(organization_schema, data)
    if errors:
        return errors
    user_ids = data['users']
    users = db.session.query(User).filter(User.id.in_(user_ids)).all()
    data['users'] = users
    organization = Organization(**data)
    organization.users.append(current_user)
    db.session.add(organization)
    db.session.commit()
    return jsonify(dict(organization_id=organization.id)), 200


# TODO: пока любой пользователь может загружать аватар организации
@api.route('/upload_organization_avatar', methods=['POST'])
@login_required
def upload_organization_avatar():
    data = request.get_json()
    photo_url, organization_id = data.get('photo_url'), data.get('organization_id')
    errors = validate_params_with_schema(OrganizationPhotoURLSchema(), data)
    if errors:
        return errors
    organization = db.session.query(Organization).filter_by(id=organization_id).first()
    # Если мы не состоим в этой организации, выкинуть ошибку
    if organization not in current_user.organizations:
        error = build_error(SwaggerResponses.ERROR_NOT_IN_ORGANIZATION, organization_id)
        return jsonify(error), 400
    # Назначаем photo_url организации
    organization.photo_url = photo_url
    db.session.commit()
    return jsonify(dict(organization_id=organization_id))
