import factory.fuzzy

from main_app.model import JoinRideRequest
from app import db


class JoinRideRequestFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = JoinRideRequest
        sqlalchemy_session = db.session
    status = factory.fuzzy.FuzzyChoice([-1, 0, 1])

    @factory.post_generation
    def user(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.user = extracted

    @factory.post_generation
    def ride(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.ride = extracted
