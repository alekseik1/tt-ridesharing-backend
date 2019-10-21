from flask_testing import TestCase
from app import create_app, db
from flask import url_for
from utils.exceptions import ResponseExamples
from model import User, Ride, Organization, Driver
from datetime import datetime
import unittest


class BaseTest(TestCase):
    def create_app(self):
        return create_app('test')

    def setUp(self) -> None:
        self.app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False
        # Re-create db
        db.session.close()
        db.drop_all()
        db.create_all()

        from views import get_user_data, login, logout, get_all_rides, get_all_organizations
        self.get_user_data_url = url_for('.' + get_user_data.__name__)
        self.get_all_rides_url = url_for('.' + get_all_rides.__name__)
        self.get_all_organizations_url = url_for('.' + get_all_organizations.__name__)
        self.login_url = url_for('.' + login.__name__)
        self.logout_url = url_for('.' + logout.__name__)
        # Add two users
        self.user1 = User(first_name='Martin', last_name='Smith', email='m.smith@gmail.com')
        self.user1.set_password('12345')
        db.session.add(self.user1)
        db.session.commit()
        self.user2 = User(first_name='User2', last_name='User2', email='user2@gmail.com')
        self.user2.set_password('12345')
        db.session.add(self.user2)
        db.session.commit()
        # Login user1
        self.client.post(self.login_url, json={'login': self.user1.email, 'password': '12345'})


class GetUserDataTests(BaseTest):

    def test_correct_data(self):
        response = self.client.get(self.get_user_data_url)
        with self.subTest('correct status code'):
            self.assert200(response)
        with self.subTest('correct data in response'):
            # TODO: validation via marshmallow lib
            correct_response = ResponseExamples.USER_INFO
            correct_response['user_id'] = self.user1.id
            correct_response['first_name'] = self.user1.first_name
            correct_response['last_name'] = self.user1.last_name
            correct_response['email'] = self.user1.email
            correct_response['photo_url'] = self.user1.photo
            self.assertEqual(correct_response, response.get_json())

    def test_no_anonymous_users(self):
        with self.client:
            self.client.post(self.logout_url)
            response = self.client.get(self.get_user_data_url)
        with self.subTest('correct status code'):
            self.assert401(response)
        with self.subTest('correct error message'):
            self.assertEqual(ResponseExamples.AUTHORIZATION_REQUIRED, response.get_json())


class GetAllRidesTests(BaseTest):

    def setUp(self) -> None:
        super().setUp()
        # Make user2 a driver
        self.driver1 = Driver(id=self.user2.id, passport_1='', passport_2='', passport_selfie='',
                              driver_license_1='', driver_license_2='')
        db.session.add(self.driver1)
        db.session.commit()

        # Add organization
        self.org1 = Organization(name='org1', latitude=3.33, longitude=3.222)
        self.org2 = Organization(name='org2', latitude=4.33, longitude=4.222)
        db.session.add_all([self.org1, self.org2])
        db.session.commit()
        self.ride1 = Ride(
            start_organization_id=self.org1.id,
            stop_organization_id=self.org2.id,
            start_time=datetime.now(),
            host_driver_id=self.driver1.id,
        )
        db.session.add(self.ride1)
        db.session.commit()
        # Login user1
        self.client.post(self.login_url, json={'login': self.user1.email, 'password': '12345'})

    def test_nothing(self):
        response = self.client.get(self.get_all_rides_url)
        pass


if __name__ == '__main__':
    unittest.main()