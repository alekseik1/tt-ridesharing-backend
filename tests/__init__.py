from flask_login import login_user, logout_user
from contextlib import contextmanager
from flask_testing import TestCase
from mimesis import Person, Address

from app import create_app, db
from main_app.model import User, Organization, Driver


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
            photo='',
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
