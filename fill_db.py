import factory
from factory.random import randgen

from app import create_app, db
from main_app.fixtures.organizations import OrganizationFactory
from main_app.fixtures.users import UserFactory
from main_app.fixtures.cars import CarFactory


def fill_database(app):
    with app.app_context():
        db.drop_all()
        db.create_all()
        # Users without cars
        users = factory.build_batch(UserFactory, 20)
        db.session.add_all(users)
        # Create 10 cars and 10 owners for them
        cars = factory.build_batch(CarFactory, 20)
        car_users = [x.owner for x in cars]
        db.session.add_all(cars)
        # We will explicitly iterate since we need full randomness
        organizations = []
        for i in range(3):
            # Take some users with cars, some without
            organizations.append(OrganizationFactory(
                users=randgen.choices(users + car_users, k=len(users + car_users)//2)
            ))
        db.session.add_all(organizations)
        db.session.commit()


if __name__ == '__main__':
    app = create_app()
    fill_database(app)
