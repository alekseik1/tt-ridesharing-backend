import factory.random
from sqlalchemy.exc import DatabaseError
from datetime import datetime, timedelta

from app import create_app, db
from main_app.fixtures.join_ride_request import JoinRideRequestFactory
from main_app.fixtures.organizations import OrganizationFactory
from main_app.fixtures.users import UserFactory, UserFeedbackFactory
from main_app.fixtures.cars import CarFactory
from main_app.fixtures.rides import RideFactory
from main_app.model import Organization


def fill_database(app):
    with app.app_context():
        db.drop_all()
        db.create_all()
        # Users without cars
        users = factory.build_batch(UserFactory, 50)
        db.session.add_all(users)
        # Create 10 cars and 10 owners for them
        cars = factory.build_batch(CarFactory, 20)
        car_users = [x.owner for x in cars]
        db.session.add_all(cars)
        # We will explicitly iterate since we don't want to create users for organizations
        organizations = []
        all_users = users + car_users
        for i in range(3):
            # Take some users with cars, some without
            organizations.append(OrganizationFactory(
                users=[all_users[j] for j in range(i, len(all_users), 3)]
            ))
        # Same for rides
        rides = []
        for i in range(5):
            rides.append(RideFactory(
                start_organization=organizations[i % len(organizations)],
                host=car_users[i % len(car_users)],
                passengers=users[3*i:3*(i+1)],
                car=car_users[i % len(car_users)].cars[0],
                start_datetime=(datetime.now() + timedelta(minutes=15)).isoformat()
            ))
        # User can join ride only via JoinRequest acceptance
        # So, we need to create corresponding JoinRequest with 'ACCEPTED' answer
        join_requests = []
        for ride in rides:
            for user in ride.passengers:
                join_requests.append(JoinRideRequestFactory(
                    ride=ride,
                    user=user,
                    status=1
                ))
        # Also, create some undecided requests to rides
        undecided_requests = []
        for ride in rides:
            for i in range(15, 20):
                undecided_requests.append(JoinRideRequestFactory(
                    ride=ride,
                    user=users[i],
                    status=0
                ))
        # Add random rating to users
        user_feedback_records = []
        for user in users:
            user_feedback_records.extend(factory.build_batch(UserFeedbackFactory, 10, user=user))
        db.session.add_all(user_feedback_records)
        db.session.add_all(organizations)
        db.session.add_all(rides)
        db.session.add_all(join_requests)
        db.session.add_all(undecided_requests)
        try:
            db.session.commit()
        except DatabaseError:
            db.session.rollback()
        # Reindex __searchable__ models
        searchable_models = (Organization, )
        for model in searchable_models:
            model.reindex()


if __name__ == '__main__':
    app = create_app()
    fill_database(app)
