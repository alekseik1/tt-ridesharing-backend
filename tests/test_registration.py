from flask_testing import TestCase
from flask import url_for
import factory
import unittest

from settings import BLUEPRINT_API_NAME
from main_app.schemas import UserIDSchema
from main_app.model import User
from main_app.views import auth
import app
from app import db
from main_app.fixtures.users import UserFactoryNoID


class BasicRegistrationTests(TestCase):

    def create_app(self):
        return app.create_app()

    def setUp(self) -> None:
        db.drop_all()
        db.create_all()
        self.url = url_for(f'{BLUEPRINT_API_NAME}.{auth.register_user.__name__}')

    def _register_random_user(self):
        user_json = factory.build(dict, FACTORY_CLASS=UserFactoryNoID)
        response = self.client.post(self.url, json=user_json)
        return response

    def test_register_many(self):
        for _ in range(10):
            response = self._register_random_user()
            # Status code
            self.assert200(response)

    def test_register_swagger_format(self):
        response = self._register_random_user()

        data = response.json
        UserIDSchema().validate(data)

    def test_register_same_emails(self):
        new_user = factory.build(dict, FACTORY_CLASS=UserFactoryNoID)
        self.client.post(self.url, json=new_user)
        # Register same user again
        response = self.client.post(self.url, json=new_user)
        self.assert400(response)

    def test_is_in_db_after_registration(self):
        response = self._register_random_user()
        self.assertIsInstance(
            db.session.query(User).filter_by(**UserIDSchema().load(response.json)).first(),
            User)


if __name__ == '__main__':
    unittest.main()
