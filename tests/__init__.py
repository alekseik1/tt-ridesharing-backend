from flask_login import login_user, logout_user
from contextlib import contextmanager
from flask_testing import TestCase
from mimesis import Person, Address, Transport, Text

from app import create_app, db
from main_app.model import User, Organization, Driver, Car
from main_app.responses import SwaggerResponses


def add_users(number=2):
    """
    Добавляет рандомных пользователей.

    :param number: Число пользователей
    :return: List <User>
    """
    result = []
    for _ in range(number):
        person = Person(locale='ru')
        user = User(
            first_name=person.name(),
            last_name=person.surname(),
            email=person.email(),
            photo_url='',
        )
        user.set_password('12345')
        db.session.add(user)
        result.append(user)
    db.session.commit()
    return result


def add_organizations(number=2):
    """
    Добавляет рандомные организации

    :param number: Число организаций
    :return: List <Organization>
    """
    result = []
    for i in range(number):
        address = Address()
        latitude, longitude = address.latitude(), address.longitude()
        organization = Organization(
            name=f'Organization{i}',
            latitude=latitude,
            longitude=longitude,
            address=f'ул. Уличная, д.1{i}'
        )
        db.session.add(organization)
        result.append(organization)
    db.session.commit()
    return result


def add_users_to_organizations(users: list, organizations: list):
    """
    Добавляет пользователей в организации линейно (т.е. одна за другой)
    :param users: List <User>
    :param organizations: List <Organization>
    :return: Список тьюплов (<User>, <Organization>)
    """
    result = []
    for i, user in enumerate(users):
        # 1, 2 идут в 1 организацию, 3, 4 идут во второую орг. и зациклить по организациям
        organization_for_user = organizations[i // 2 % len(organizations)]
        user.organizations.append(organization_for_user)
        result.append((user, organization_for_user))
    db.session.commit()
    return result


def _generate_car_number():
    import random
    gen_char = lambda: chr(random.randint(ord('А'), ord('Я')))
    return '{s1}{number}{s2} {code}{country}'.format(
        s1=gen_char(),
        number=random.randint(100, 999),
        s2=f'{gen_char()}{gen_char()}',
        code=random.randint(10, 777),
        country='RUS'
    )


def add_cars_to_drivers(drivers):
    result = []
    for i in range(len(drivers)):
        car_model = Transport().car()
        car_number = _generate_car_number()
        car_color = Text(locale='ru').color()
        car = Car(model=car_model, color=car_color, registry_number=car_number, owner=drivers[i])
        db.session.add(car)
        result.append(car)
    db.session.commit()
    return result


def register_drivers(users_to_register: list):
    """
    Регает водителей на основе <User>
    :param users_to_register: List <User>
    :return: List <Driver>
    """
    result = []
    for user in users_to_register:
        driver = Driver(
            id=user.id,
            license_1='',
            license_2='',
        )
        db.session.add(driver)
        result.append(driver)
    db.session.commit()
    return result


class BaseTest(TestCase):

    def create_app(self):
        return create_app('test')

    def setUp(self) -> None:
        self.app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False
        # Re-create db
        db.session.close()
        db.drop_all()
        db.create_all()
        self.users = add_users(number=10)
        self.organizations = add_organizations(number=2)
        self.user_organizations = add_users_to_organizations(self.users, self.organizations)
        # Каждого второго сделаем водителем. У каждой организации как минимум 1 водитель и 1 пассажир
        self.drivers = register_drivers(self.users[::2])
        # На каждого водителя - по автомобилю
        self.cars = add_cars_to_drivers(self.drivers)
        # Не-водители
        self.single_users = self.users[1::2]

    @contextmanager
    def login_as(self, user):
        from main_app.views.auth import login, logout
        from flask import url_for
        # Log in
        self.client.post(url_for(f'api.{login.__name__}'), json=dict(
            login=user.email,
            password='12345',
        ))
        yield user
        # Log out in the end
        self.client.post(url_for(f'api.{logout.__name__}'))

    @staticmethod
    def invalid_parameters_generator(correct_data):
        from itertools import combinations
        keys = list(correct_data.keys())
        # Допускаем взять 1..N-1 ключей запроса
        for i in range(1, len(keys)):
            # Состовляем все возможные способы выкинуть i элементов
            for keys_combo in combinations(keys, i):
                # Возвращаем их
                yield {key: correct_data[key] for key in keys_combo}

    def routine_invalid_parameters_for(self, endpoint, correct_request):
        for incorrect_request in self.invalid_parameters_generator(correct_request):
            response = self.client.post(endpoint, json=incorrect_request)
            removed_keys = sorted(list(set(correct_request.keys()) - set(incorrect_request.keys())))
            with self.subTest(f'Removed {removed_keys}'):
                self.assert400(response)
                self.assertEqual(
                    SwaggerResponses.some_params_are_invalid(removed_keys),
                    response.get_json()
                )
