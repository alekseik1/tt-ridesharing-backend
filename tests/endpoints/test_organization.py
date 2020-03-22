from flask_testing import TestCase
from flask import url_for

from app import create_app, db
from settings import BLUEPRINT_API_NAME
from main_app.views.organization import organization as endpoint
from main_app.schemas import OrganizationJsonSchema, IdSchema
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
        schema = OrganizationJsonSchema()

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
        with self.subTest('correct request'):
            with login_as(self.client, db.session.query(User).first()):
                response = self.client.post(self.url, json=json)
            self.assert200(response)
            IdSchema().load(response.json)
