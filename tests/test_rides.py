import unittest
from datetime import datetime

from app import db
from model import Driver, Organization, Ride, OrganizationSchema
from tests.test_get_info import BaseTest
from utils.exceptions import ResponseExamples


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
        self.start_time = datetime.now()
        self.ride1 = Ride(
            start_organization_id=self.org1.id,
            stop_organization_id=self.org2.id,
            start_time=self.start_time,
            host_driver_id=self.driver1.id,
        )
        db.session.add(self.ride1)
        db.session.commit()
        # Login user1
        self.client.post(self.login_url, json={'login': self.user1.email, 'password': '12345'})

    def test_correct_response(self):
        response = self.client.get(self.get_all_rides_url)
        organization_schema = OrganizationSchema()
        correct_response = ResponseExamples.RIDE_INFO
        correct_response['host_driver_id'] = self.driver1.id
        correct_response['start_time'] = str(self.start_time)
        correct_response['start_organization'] = organization_schema.dump(self.org1)
        correct_response['stop_organization'] = organization_schema.dump(self.org2)
        correct_response['passengers'] = []
        with self.subTest('status code'):
            self.assert200(response)
        with self.subTest('correct data'):
            self.assertEqual(correct_response, response.get_json()[0])

    def test_unauthorized(self):
        logout_response = self.client.post(self.logout_url)
        response = self.client.get(self.get_all_rides_url)
        correct_response = ResponseExamples.AUTHORIZATION_REQUIRED
        with self.subTest('status code'):
            self.assert401(response)
        with self.subTest('correct error'):
            self.assertEqual(correct_response, response.get_json())


if __name__ == '__main__':
    unittest.main()
