from flask import url_for
import unittest

from settings import BLUEPRINT_API_NAME
from main_app.schemas import UserIDSchema
from main_app.model import User
from main_app.views import auth
from app import db
from . import TestWithDatabase


class BasicRegistrationTests(TestWithDatabase):

    def setUp(self) -> None:
        super().setUp()
        self.url = url_for(f'{BLUEPRINT_API_NAME}.{auth.register_user.__name__}')

    def _register_fixture(self):
        user_json = {'email': 'registered@gmail.com',
                     'password': '12345',
                     'phoneNumber': '+7 (950) 001-01-01',
                     'firstName': 'Yaya',
                     'lastName': 'Test'}
        response = self.client.post(self.url, json=user_json)
        return response

    def test_register_swagger_format(self):
        response = self._register_fixture()

        data = response.json
        UserIDSchema().validate(data)

    def test_register_same_emails(self):
        self._register_fixture()
        response = self._register_fixture()
        self.assert400(response)

    def test_is_in_db_after_registration(self):
        response = self._register_fixture()
        self.assertIsInstance(
            db.session.query(User).filter_by(**UserIDSchema().load(response.json)).first(),
            User)


if __name__ == '__main__':
    unittest.main()
