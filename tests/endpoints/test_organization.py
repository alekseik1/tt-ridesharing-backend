from flask import url_for
import unittest

from app import db
from settings import BLUEPRINT_API_NAME
from main_app.views.organization import organization as endpoint
from main_app.schemas import OrganizationJsonSchema, IdSchema, UserJsonSchema
from main_app.exceptions.custom import NotInOrganization, CreatorCannotLeave
from tests import login_as
from main_app.model import Organization, User
from . import TestWithDatabase


class BasicTest(TestWithDatabase):

    def setUp(self):
        super().setUp()
        self.url = url_for(f'{BLUEPRINT_API_NAME}.{endpoint.__name__}')

    def test_get_organization(self):
        ID = 1
        with login_as(self.client, db.session.query(User).first()):
            response = self.client.get(self.url, query_string={
                'id': ID
            })
        organization = db.session.query(Organization).filter_by(id=ID).first()
        schema = OrganizationJsonSchema(only=(
            'name', 'address',
            'creator', 'last_ride_datetime',
            'id', 'photo_url',
            'total_members', 'total_drivers',
            'min_ride_cost', 'max_ride_cost',
            'latitude', 'longitude',
            'description',
        ))

        self.assert200(response)
        self.assertEqual(schema.dump(organization), response.json)

    def test_put_organization(self):
        json = {
            'name': 'org1',
            'latitude': -10.0,
            'longitude': 10.0,
            'controlQuestion': 'Whatsapp?',
            'controlAnswer': 'Gut',
        }
        with login_as(self.client, db.session.query(User).first()):
            response = self.client.put(self.url, json=json)
        self.assert200(response)
        IdSchema().load(response.json)

    def test_post_organization(self):
        ID = 1
        json = {
            'id': ID,
            'name': 'Brave new name',
            'description': 'I\'m new description!',
            'photoUrl': 'https://photos.com/1.jpg',
        }
        org_owner = db.session.query(Organization).filter_by(id=ID).first().creator
        not_owner = db.session.query(User).filter(User.id != org_owner.id).first()
        with self.subTest('Correct response from owner'):
            with login_as(self.client, org_owner):
                response = self.client.post(self.url, json=json)
            self.assert200(response)
            IdSchema().load(response.json)
        with self.subTest('Forbidden for non-owner'):
            with login_as(self.client, not_owner):
                response = self.client.post(self.url, json=json)
            self.assert403(response)

    @unittest.skip('DELETE is broken, needs DB investigation')
    def test_delete_organization(self):
        ID = 1
        json = {
            'id': ID
        }
        org_owner = db.session.query(Organization).filter_by(id=ID).first().creator
        not_owner = db.session.query(User).filter(User.id != org_owner.id).first()
        with self.subTest('Correct response from owner'):
            with login_as(self.client, org_owner):
                response = self.client.delete(self.url, json=json)
            self.assert200(response)
        with self.subTest('Forbidden for non-owner'):
            with login_as(self.client, not_owner):
                response = self.client.delete(self.url, json=json)
            self.assert403(response)

    def test_organization_members(self):
        ID = 1
        query_params = {
            'id': ID
        }
        with login_as(self.client, db.session.query(User).first()):
            response = self.client.get(f'{self.url}/members', query_string=query_params)
            self.assert200(response)
            # Response content check
            self.assertEqual({'id', 'members'}, response.json.keys())
            UserJsonSchema(
                session=db.session,
                only=('id', 'first_name', 'last_name', 'photo_url'),
                # `rating` is dump_only, so we need to handle it separately
                unknown=('rating',),
                many=True
            ).load(response.json['members'])

    def test_organization_question_get(self):
        ID = 1
        query_params = {
            'id': ID
        }
        with login_as(self.client, db.session.query(User).first()):
            response = self.client.get(f'{self.url}/question', query_string=query_params)
            self.assert200(response)
            OrganizationJsonSchema(only=('id', 'control_question')).load(response.json)

    def _everything_is_fine_for(self, user, org):
        with login_as(self.client, user):
            response = self.client.post(f'{self.url}/join', json={
                'id': org.id, 'controlAnswer': org.control_answer
            })
            self.assert200(response)
            OrganizationJsonSchema(only=('id',)).load(response.json)

    def test_already_in_organization(self):
        org = db.session.query(Organization).filter_by(id=1).first()
        self._everything_is_fine_for(org.users[0], org)

    def test_not_in_organization(self):
        org = db.session.query(Organization).filter_by(id=1).first()
        user = db.session.query(User).filter(
            User.id.notin_([x.id for x in org.users])
        ).first()
        self._everything_is_fine_for(user, org)

    def test_incorrect_control_answer(self):
        ID = 1
        org = db.session.query(Organization).filter_by(id=ID).first()
        user = db.session.query(User).filter(
            User.id.notin_([x.id for x in org.users])
        ).first()
        with login_as(self.client, user):
            response = self.client.post(f'{self.url}/join', json={
                'id': ID, 'controlAnswer': f'INCORRECT {org.control_answer}'
            })
            self.assert400(response)

    def test_leave_organization(self):
        ID = 1
        org = db.session.query(Organization).filter_by(id=ID).first()
        creator = org.creator
        non_creator = (set(org.users) - {creator}).pop()
        non_member = (set(db.session.query(User).all()) - set(org.users)).pop()

        def make_request():
            return self.client.post(f'{self.url}/leave', json={
                'id': ID
            })

        with self.subTest('Simple member'):
            with login_as(self.client, non_creator):
                response = make_request()
                self.assert200(response)
        with self.subTest('Creator cannot leave'):
            with login_as(self.client, creator):
                response = make_request()
                self.assert400(response)
                # Error message
                self.assertEqual(CreatorCannotLeave.description, response.json.get('description'))
        with self.subTest('Not member raises error'):
            with login_as(self.client, non_member):
                response = make_request()
                self.assert403(response)
                # Error message
                self.assertEqual(NotInOrganization.description, response.json.get('description'))
