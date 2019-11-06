from flask import url_for
from tests import BaseTest
from app import db
from main_app.model import User, Driver
from main_app.schemas import CarSchema, CarIdSchema
import unittest


class TestCar(BaseTest):

    def setUp(self) -> None:
        super().setUp()
        from main_app.views.car import get_my_cars, register_car_for_driver
        self.get_my_cars_url = url_for(f'api.{get_my_cars.__name__}')
        self.register_car_for_driver_url = url_for(f'api.{register_car_for_driver.__name__}')

    def test_get_my_cars(self):
        car_schema = CarSchema(many=True)
        for driver in self.drivers:
            with self.subTest(f'{driver} cars'):
                user = db.session.query(User).filter_by(id=driver.id).first()
                with self.login_as(user):
                    response = self.client.get(self.get_my_cars_url)
                    self.assert200(response)
                    self.assertEqual(
                        0,
                        len(car_schema.validate(response.get_json(), session=db.session))
                    )

    def test_register_car_for_driver_correct_request(self):
        request_template = dict(
            model='Mazda',
            color='Красный',
            registry_number='К234РП 777',
            owner_id=None
        )
        for driver in self.drivers:
            with self.subTest(f'{driver} is getting new car...'):
                user = db.session.query(User).filter_by(id=driver.id).first()
                with self.login_as(user):
                    correct_request = request_template
                    correct_request['owner_id'] = driver.id
                    response = self.client.post(self.register_car_for_driver_url, json=correct_request)
                    car_id_schema = CarIdSchema()
                    self.assert200(response)
                    self.assertEqual(0, len(car_id_schema.validate(response.get_json(), session=db.session)))

    def test_register_car_for_driver_incorrect_request(self):
        driver = self.drivers[0]
        correct_request = dict(
            model='Mazda',
            color='Красный',
            registry_number='К234РП 777',
            owner_id=driver.id
        )
        user = db.session.query(User).filter_by(id=driver.id).first()
        with self.login_as(user):
            self.routine_invalid_parameters_for(self.register_car_for_driver_url, correct_request)


if __name__ == '__main__':
    unittest.main()
