from flask import request, jsonify
from flask_login import login_required, current_user

from app import db
from main_app.model import Organization
from main_app.schemas import OrganizationSchemaUserInfo,\
    IdSchema, OrganizationJsonSchema, JoinOrganizationSchema, OrganizationPermissiveSchema
from main_app.exceptions.custom import IncorrectControlAnswer, \
    NotInOrganization, CreatorCannotLeave, InsufficientPermissions
from main_app.views import api
from main_app.misc import reverse_geocoding_blocking


@api.route('/organization', methods=['GET', 'POST', 'PUT'])
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
        org = OrganizationPermissiveSchema().load(request.json)
        if current_user != org.creator:
            raise InsufficientPermissions()
        # Update address
        # NOTE: maybe move it to DB hooks?
        org.address = reverse_geocoding_blocking(
            latitude=org.latitude, longitude=org.longitude
        )['address']
        db.session.add(org)
        db.session.commit()
        return IdSchema().dump(org)


@api.route('/organization/members', methods=['GET'])
@login_required
def organization_members():
    return OrganizationJsonSchema(only=('id', 'users')).dump(
        db.session.query(Organization).filter_by(**IdSchema().load(request.args)).first()
    )


@api.route('/organization/question', methods=['GET'])
@login_required
def question():
    return OrganizationJsonSchema(only=('id', 'control_question')).dump(
        db.session.query(Organization).filter_by(**IdSchema().load(request.args)).first()
    )


@api.route('/organization/join', methods=['POST'])
@login_required
def join():
    data = JoinOrganizationSchema().load(request.json)
    org = db.session.query(Organization).filter_by(id=data['id']).first()
    if org.control_answer != data['control_answer']:
        raise IncorrectControlAnswer()
    if current_user not in org.users:
        org.users.append(current_user)
        db.session.commit()
    return IdSchema().dump(org)


@api.route('/organization/leave', methods=['POST'])
@login_required
def leave():
    org = db.session.query(Organization).filter_by(**IdSchema().load(request.json)).first()
    if org not in current_user.organizations:
        raise NotInOrganization()
    if current_user == org.creator:
        raise CreatorCannotLeave()
    org.users.remove(current_user)
    db.session.commit()
    return {}


@api.route('/get_all_organizations', methods=['GET'])
@login_required
def get_all_organizations():
    organization_schema = OrganizationSchemaUserInfo(many=True)
    result = organization_schema.dump(db.session.query(Organization).all(), many=True)
    return jsonify(result), 200
