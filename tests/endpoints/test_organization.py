from flask_testing import TestCase
from flask import url_for

from app import create_app, db
from settings import BLUEPRINT_API_NAME
from main_app.views.organization import organization as endpoint
from main_app.schemas import OrganizationJsonSchema
from main_app.model import Organization
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
        response = self.client.get(self.url, query_string={'id': ID})
        organization = db.session.query(Organization).filter_by(id=ID).first()
        schema = OrganizationJsonSchema()

        self.assert200(response)
        self.assertEqual(schema.dump(organization), response.json)
