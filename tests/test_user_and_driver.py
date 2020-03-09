import unittest
from flask import url_for
from main_app.model import User, Driver
from app import db

from main_app.responses import SwaggerResponses, build_error
from main_app.schemas import UserSchemaOrganizationInfo
from tests import BaseTest


class TestUserAndDriver(BaseTest):

    def setUp(self):
        from main_app.views.user_and_driver import get_user_info, am_i_driver, register_driver
        super().setUp()
        self.get_user_info_url = url_for(f'api.{get_user_info.__name__}')
        self.am_i_driver_url = url_for(f'api.{am_i_driver.__name__}')
        self.user_schema = UserSchemaOrganizationInfo()

    def test_get_user_info(self):
        # Correct data for each user
        for user in self.users:
            with self.subTest(f'{user} data and status code'):
                with self.login_as(user):
                    response = self.client.get(self.get_user_info_url)
                    self.assert200(response)
                    # FIXME: broken after specification changes
                    #correct_response = self.user_schema.dump(user)
                    #self.assertEqual(correct_response, response.get_json())

    def test_get_user_info_anonymous_user(self):
        # No anonymous users
        # Request outside 'login_as' context
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


class TestDriverMethods(BaseTest):

    def setUp(self):
        from main_app.views.user_and_driver import register_driver
        super().setUp()
        self.register_driver_url = url_for(f'api.{register_driver.__name__}')
        self.user = self.single_users[0]

    def test_register_driver_correct_request(self):
        with self.login_as(self.user):
            response = self.client.post(self.register_driver_url, json=dict(
                id=self.user.id,
                license_1='license_1',
                license_2='license_2',
            ))
            self.assert200(response, message=response.get_json())
            correct_response = dict(user_id=self.user.id)
            self.assertEqual(correct_response, response.get_json())

    def test_register_driver_anonymous_user(self):
        response = self.client.post(self.register_driver_url, json=dict(
            id=self.user.id,
            license_1='license_1',
            license_2='license_2',
        ))
        self.assert401(response, message=response.get_json())
        correct_response = build_error(SwaggerResponses.AUTHORIZATION_REQUIRED)
        self.assertEqual(correct_response, response.get_json())

    def test_register_driver_incorrect_parameters(self):
        correct_request = dict(id=self.user.id, license_1='l1', license_2='l2')
        with self.login_as(self.user):
            self.routine_invalid_parameters_for(self.register_driver_url, correct_request)

    def test_register_driver_two_times(self):
        request = dict(id=self.user.id, license_1='l1', license_2='l2')
        with self.login_as(self.user):
            response = self.client.post(self.register_driver_url, json=request)
            response = self.client.post(self.register_driver_url, json=request)
            self.assert400(response)
            correct_response = SwaggerResponses.some_params_are_invalid(['id'])
            self.assertEqual(correct_response, response.get_json())

    def test_register_driver_another_user(self):
        fake_id = self.users[-1].id
        request = dict(id=fake_id, license_1='l1', license_2='l2')
        with self.login_as(self.user):
            response = self.client.post(self.register_driver_url, json=request)
            self.assert403(response)
            correct_response = SwaggerResponses.NO_PERMISSION_FOR_USER
            correct_response['value'] = fake_id
            self.assertEqual(correct_response, response.get_json())


class TestUserRegistration(BaseTest):

    def setUp(self):
        super().setUp()
        from main_app.views.auth import register_user
        self.register_user_url = url_for(f'api.{register_user.__name__}')
        self.correct_request = dict(
            first_name='Aleksei',
            last_name='Testovksy',
            email='a.testovsky@gmail.com',
            password='12345',
            phone_number='+7 (950) 005-94-75'
        )

    def test_register_user_incorrect_parameters(self):
        self.routine_invalid_parameters_for(self.register_user_url, self.correct_request)

    def test_register_user_correct_request(self):
        response = self.client.post(self.register_user_url, json=self.correct_request)
        self.assert200(response)
        self.assertIsNotNone(response.get_json().get('user_id'))

    def test_register_user_same_email(self):
        response = self.client.post(self.register_user_url, json=self.correct_request)
        response = self.client.post(self.register_user_url, json=self.correct_request)
        self.assert400(response)
        correct_response = SwaggerResponses.some_params_are_invalid(['email'])
        self.assertEqual(correct_response, response.get_json())


if __name__ == '__main__':
    unittest.main()
