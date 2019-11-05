import unittest
from flask import url_for
from main_app.model import User, Driver
from app import db

from main_app.responses import SwaggerResponses
from main_app.schemas import UserSchema
from tests import BaseTest


class TestGetUserInfo(BaseTest):

    def setUp(self):
        from main_app.views.user_and_driver import get_user_info, am_i_driver
        super().setUp()
        self.get_user_info_url = url_for(f'api.{get_user_info.__name__}')
        self.am_i_driver_url = url_for(f'api.{am_i_driver.__name__}')
        self.user_schema = UserSchema()

    def test_get_user_info(self):
        # Correct data for each user
        for user in self.users:
            with self.subTest(f'{user} data and status code'):
                with self.login_as(user):
                    response = self.client.get(self.get_user_info_url)
                    self.assert200(response)
                    correct_response = self.user_schema.dump(user)
                    self.assertEqual(correct_response, response.get_json())
        # No anonymous users
        # Request outside 'login_as' context
        with self.subTest('Anonymous user'):
            response = self.client.get(self.get_user_info_url)
            self.assert401(response)
            self.assertEqual(SwaggerResponses.AUTHORIZATION_REQUIRED, response.get_json())

    def test_am_i_driver(self):
        for user in self.users:
            with self.subTest(f'{user} is driver?'):
                with self.login_as(user):
                    response = self.client.get(self.am_i_driver_url)
                    self.assert200(response)
                    correct_response = dict(
                        is_driver=db.session.query(Driver).filter_by(id=user.id).first() is not None
                    )
                    self.assertEqual(correct_response, response.get_json())


if __name__ == '__main__':
    unittest.main()
