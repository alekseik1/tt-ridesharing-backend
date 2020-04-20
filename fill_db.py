import factory.random
from datetime import timedelta
from typing import List

from app import create_app, db
from main_app.fixtures.join_ride_request import JoinRideRequestFactory
from main_app.fixtures.organizations import OrganizationFactory
from main_app.fixtures.users import UserFactory
from main_app.fixtures.rides import RideFactory
from main_app.model import Organization


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
        print(f'Юзер без всего: {user_no_car.id}')
        print(f'Юзеры в организации, без машин: {[x.id for x in users_org_no_car]}')
        print(f'Юзер в организации, с машиной, не хостил: {user_org_nohost.id}')
        print(f'Юзер в организации, с машиной, хостил, '
              f'нет реквестов: {user_org_host_norequests.id}')
        print(f'Юзер в организации, с машиной, хостил, '
              f'не ответил на реквесты: {user_org_host_notdecided.id}')
        print(f'Юзер в организации, с машиной, хостил, '
              f'все принял: {user_org_host_accepted.id}')
        print(f'Юзер в организации, с машиной, хостил, '
              f'все отклонил: {user_org_host_declined.id}')
        print(f'Юзер в организации, с машиной, хостил, '
              f'есть завершенная поездка: {user_org_host_finished.id}')


if __name__ == '__main__':
    app = create_app()
    fill_database(app)
