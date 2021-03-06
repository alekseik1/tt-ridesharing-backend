import factory.random
from datetime import timedelta
from typing import List
import sys

from app import create_app, db
from main_app.fixtures.join_ride_request import JoinRideRequestFactory
from main_app.fixtures.organizations import OrganizationFactory
from main_app.fixtures.users import UserFactory
from main_app.fixtures.rides import RideFactory
from main_app.model import Organization


def clean_firebase():
    # NOTE: can have `has_next_page` == True - need to implement all pages reading
    import firebase_admin
    from firebase_admin import credentials
    from firebase_admin.auth import list_users, delete_user

    cred = credentials.Certificate("firebase_creds.json")
    firebase_admin.initialize_app(cred)
    for user in list_users().users:
        delete_user(user.uid)


def fill_database(app):
    with app.app_context():
        db.drop_all()
        db.create_all()
        #    - [x] Юзер без всего
        user_no_car = UserFactory(cars=[])
        db.session.add(user_no_car)
        db.session.commit()

        orgs = factory.build_batch(OrganizationFactory, 1)  # type: List[Organization]
        for org in orgs:
            #    - [x] Юзер в организации, без тачки
            users_org_no_car = factory.build_batch(UserFactory, 12, cars=[])
            org.users.extend(users_org_no_car)

            #    - [x] Юзер в организации с тачкой, не хостил
            user_org_nohost = UserFactory()
            org.users.append(user_org_nohost)

            #    - [x] Юзер в организации с тачкой, хостил, нет реквестов
            user_org_host_norequests = UserFactory()
            org.users.append(user_org_host_norequests)
            for from_organization in [True, False]:
                ride = RideFactory(
                    organization=org,
                    host=user_org_host_norequests,
                    passengers=[],
                    from_organization=from_organization
                )
                db.session.add(ride)

                #    - [x] Юзер в организации с тачкой, хостил, реквесты не рассмотрел
                user_org_host_notdecided = UserFactory()
                org.users.append(user_org_host_notdecided)
                ride_nodecided = RideFactory(
                    organization=org,
                    host=user_org_host_notdecided,
                    passengers=[],
                    from_organization=from_organization
                )
                db.session.add(ride_nodecided)
                # Первые три кинул заявки, их проигнорят
                for user in users_org_no_car[:3]:
                    db.session.add(JoinRideRequestFactory(
                        status=0,
                        user=user,
                        ride=ride_nodecided
                    ))

                #    - [x] Юзер в организации с тачкой, хостил, реквесты все принял
                user_org_host_accepted = UserFactory()
                org.users.append(user_org_host_accepted)
                ride_accepted = RideFactory(
                    organization=org,
                    host=user_org_host_accepted,
                    # Троих приняли
                    passengers=users_org_no_car[3:6],
                    from_organization=from_organization
                )
                db.session.add(ride_accepted)
                for user in users_org_no_car[3:6]:
                    db.session.add(JoinRideRequestFactory(
                        status=1,
                        user=user,
                        ride=ride_accepted
                    ))

                #    - [x] Юзер в организации с тачкой, хостил, реквесты все отклонил
                user_org_host_declined = UserFactory()
                org.users.append(user_org_host_declined)
                ride_declined = RideFactory(
                    organization=org,
                    host=user_org_host_declined,
                    passengers=[],
                    from_organization=from_organization
                )
                db.session.add(ride_declined)
                for user in users_org_no_car[6:9]:
                    db.session.add(JoinRideRequestFactory(
                        status=-1,
                        user=user,
                        ride=ride_declined
                    ))

                #     - [x] Юзер в организации с тачкой, хостил, есть завершенная поездка
                user_org_host_finished = UserFactory()
                org.users.append(user_org_host_finished)
                ride_finished = RideFactory(
                    organization=org,
                    host=user_org_host_finished,
                    # С 9 по 12 прокатились успешно
                    passengers=users_org_no_car[9:12],
                    from_organization=from_organization,
                )
                ride_finished.stop_datetime = ride_finished.start_datetime + timedelta(minutes=40)
                db.session.add(ride_finished)
                for user in users_org_no_car[9:12]:
                    db.session.add(JoinRideRequestFactory(
                        status=1,
                        user=user,
                        ride=ride_finished
                    ))
                db.session.commit()
        db.session.add_all(orgs)
        db.session.commit()


if __name__ == '__main__':
    app = create_app()
    if len(sys.argv) == 2:
        clean_firebase()
    fill_database(app)
