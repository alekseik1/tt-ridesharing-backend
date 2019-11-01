import unittest
from datetime import datetime

from app import db
from main_app.model import Driver, Organization, Ride
from main_app.schemas import OrganizationSchema
from tests.test_get_info import BaseTest
from main_app.responses import SwaggerResponses


class RidesBaseTest(BaseTest):

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
            stop_longitude=0.0,
            stop_latitude=0.0,
            start_time=self.start_time,
            host_driver_id=self.driver1.id,
        )
        db.session.add(self.ride1)
        db.session.commit()
        # Login user1
        self.client.post(self.login_url, json={'login': self.user1.email, 'password': '12345'})


class GetAllRidesTests(RidesBaseTest):

    def test_correct_response(self):
        response = self.client.get(self.get_all_rides_url)
        organization_schema = OrganizationSchema()
        correct_response = SwaggerResponses.RIDE_INFO
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
        correct_response = SwaggerResponses.AUTHORIZATION_REQUIRED
        with self.subTest('status code'):
            self.assert401(response)
        with self.subTest('correct error'):
            self.assertEqual(correct_response, response.get_json())


class JoinRideTests(RidesBaseTest):

    def test_simple_join(self):
        request_data = SwaggerResponses.RIDE_ID
        request_data['ride_id'] = self.ride1.id
        response = self.client.post(self.join_ride_url, json=request_data)
        with self.subTest('correct status code'):
            self.assert200(response)
        with self.subTest('correct return data'):
            self.assertEqual(request_data, response.get_json())
        with self.subTest('user is in passengers'):
            passengers = db.session.query(Ride).filter_by(id=self.ride1.id).first().passengers
            self.assertTrue(self.user1 in passengers)


if __name__ == '__main__':
    unittest.main()
