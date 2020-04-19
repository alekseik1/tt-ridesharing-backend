import factory.fuzzy
from datetime import datetime, timedelta

from main_app.model import Ride, RideFeedback
from app import db


class RideFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Ride
        sqlalchemy_session = db.session
    latitude = factory.fuzzy.FuzzyFloat(55.0, 56.0)
    longitude = factory.fuzzy.FuzzyFloat(37.0, 38.0)
    submit_datetime = datetime.now().isoformat()
    start_datetime = datetime.now() + timedelta(minutes=factory.fuzzy.random.randgen.randint(5, 10))
    from_organization = factory.Iterator([True, False])

    total_seats = factory.fuzzy.FuzzyChoice([4, 6])
    price = factory.fuzzy.FuzzyChoice([200, 400, 350])
    host = factory.SubFactory('.users.UserFactory')
    car = factory.LazyAttribute(lambda o: o.host.cars[0])
    car_id = factory.SelfAttribute('car.id')
    description = factory.fuzzy.FuzzyChoice(['no smoke', 'have children chair', 'talk a lot'])
    is_active = True

    @factory.post_generation
    def organization(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.organization = extracted

    @factory.post_generation
    def passengers(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for user in extracted:
                self.passengers.append(user)


class RideFeedbackFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = RideFeedback
        sqlalchemy_session = db.session
        exclude = ['id', ]

    @factory.post_generation
    def ride(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.ride = extracted
