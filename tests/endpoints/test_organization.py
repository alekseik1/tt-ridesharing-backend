from flask_testing import TestCase
from flask import url_for

from app import create_app, db
from settings import BLUEPRINT_API_NAME
from main_app.views.organization import organization as endpoint
from main_app.schemas import OrganizationJsonSchema, IdSchema, UserJsonSchema
from tests import login_as
from main_app.model import Organization, User
from fill_db import fill_database


class BasicTest(TestCase):

    def create_app(self):
        app = create_app()
        app.config['LOGIN_DISABLED'] = True
        return app

    def setUp(self):
        fill_database(self.app)
        self.url = url_for(f'{BLUEPRINT_API_NAME}.{endpoint.__name__}')

    def test_get_organization(self):
        ID = 1
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
            OrganizationJsonSchema(session=db.session, only=('id', 'control_question')).load(response.json)
