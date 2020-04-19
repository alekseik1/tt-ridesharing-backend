import factory.fuzzy
from factory.random import randgen

from main_app.model import Car
import mimesis
from app import db


class CarFactory(factory.alchemy.SQLAlchemyModelFactory):

    class Meta:
        model = Car
        sqlalchemy_session = db.session
    model = factory.Sequence(lambda n: mimesis.Transport().car())
    color = factory.fuzzy.FuzzyChoice(['red', 'greed', 'grey'])
    registry_number = factory.Sequence(
        lambda n: f'К{randgen.randint(100, 999)}ХР779'
    )
    owner = None
    owner_id = factory.SelfAttribute('owner.id')
