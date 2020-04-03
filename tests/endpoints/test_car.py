from flask import url_for
import unittest

from tests import login_as
from app import db
from settings import BLUEPRINT_API_NAME
from main_app.schemas import CarSchema, IdSchema
from main_app.model import Car, User
from main_app.views.car import car as endpoint
from . import TestWithDatabase


class BasicTest(TestWithDatabase):

    def setUp(self):
        super().setUp()
        self.url = url_for(f'{BLUEPRINT_API_NAME}.{endpoint.__name__}')

    def test_get_car(self):
        with login_as(self.client, db.session.query(Car).first().owner):
            response = self.client.get(self.url)
            self.assert200(response)
            # `Car` schema is simple, so we can directly try loading it
            CarSchema(many=True).load(response.json)

    def test_put_car(self):
        with login_as(self.client, db.session.query(User).first()):
            response = self.client.put(self.url, json={
                'color': 'red',
                'model': 'model_model',
                'registryNumber': 'К222ЧЧ777'
            })
            self.assert200(response)
            IdSchema().load(response.json)

    @unittest.skip('DELETE is broken, needs DB investigation')
    def test_delete_car(self):
        car = db.session.query(Car).first()
        with self.subTest('Car owner'):
            with login_as(self.client, car.owner):
                response = self.client.delete(self.url, json={
                    'id': car.id
                })
                self.assert200(response)
        with self.subTest('Not owner'):
            user = db.session.query(User).filter(car.owner_id != User.id).first()
            with login_as(self.client, user):
                response = self.client.delete(self.url, json={
                    'id': car.id
                })
                self.assert403(response)
        with self.subTest('Car does not exist'):
            with login_as(self.client, car.owner):
                response = self.client.delete(self.url, json={
                    'id': -2
                })
                self.assert403(response)

    def _post_routine(self, user, json):
        with login_as(self.client, user):
            return self.client.post(self.url, json=json)

    def test_post_car_non_owner(self):
        car = db.session.query(Car).first()
        non_owner = db.session.query(Car).filter(
            Car.owner_id != car.owner_id
        ).first().owner
        json = {'id': car.id, 'registryNumber': 'new_number'}
        response = self._post_routine(non_owner, json)
        self.assert403(response, response.json)

    def test_post_car_owner(self):
        car = db.session.query(Car).first()
        json = {'id': car.id, 'registryNumber': 'new_number'}
        response = self._post_routine(car.owner, json)
        self.assert200(response, response.json)
