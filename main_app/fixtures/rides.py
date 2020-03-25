import factory.fuzzy
from datetime import datetime

from main_app.model import Ride
from main_app.fixtures.cars import CarFactory
from app import db


class RideFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Ride
        sqlalchemy_session = db.session
        exclude = ['id', ]
    stop_latitude = factory.fuzzy.FuzzyFloat(55.0, 56.0)
    stop_longitude = factory.fuzzy.FuzzyFloat(37.0, 38.0)
    submit_datetime = datetime.now().isoformat()

    total_seats = factory.fuzzy.FuzzyChoice([4, 6])
    price = factory.fuzzy.FuzzyChoice([200, 400, 350])
    car = factory.SubFactory(CarFactory)
    car_id = factory.SelfAttribute('car.id')
    description = factory.fuzzy.FuzzyChoice(['no smoke', 'have children chair', 'talk a lot'])
    is_active = True

    @factory.post_generation
    def start_organization(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.start_organization = extracted

    @factory.post_generation
    def host(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.host = extracted

    @factory.post_generation
    def passengers(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for user in extracted:
                self.passengers.append(user)
