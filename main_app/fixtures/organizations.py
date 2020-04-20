import factory.fuzzy
import factory.random
from main_app.model import Organization
from app import db
import mimesis
from .users import UserFactory
from main_app.misc import reverse_geocoding_blocking


class OrganizationFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Organization
        sqlalchemy_session = db.session
    name = factory.Sequence(lambda n: f'{mimesis.Food().dish()} restaurant')
    latitude = factory.fuzzy.FuzzyFloat(55.0, 56.0)
    longitude = factory.fuzzy.FuzzyFloat(37.0, 38.0)
    address = factory.lazy_attribute(
        lambda o: reverse_geocoding_blocking(
            latitude=o.latitude, longitude=o.longitude)['address']
    )
    description = factory.Sequence(lambda n: f'Not fastfood')
    creator = factory.SubFactory(UserFactory)
    creator_id = factory.SelfAttribute('creator.id')
    control_question = 'What can change the nature of the man?'
    control_answer = factory.fuzzy.FuzzyChoice(['faith', 'suffering', 'love', 'nothing'])

    @factory.post_generation
    def users(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for user in extracted:
                self.users.append(user)
