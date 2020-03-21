import factory
from mimesis import Person

from app import db
from main_app.controller import parse_phone_number
from main_app.model import User


class UserFactoryNoID(factory.alchemy.SQLAlchemyModelFactory):

    class Meta:
        model = User
        sqlalchemy_session = db.session
        exclude = ['id', ]
    first_name = factory.Sequence(lambda n: Person().name())
    last_name = factory.Sequence(lambda n: Person().surname())
    email = factory.Sequence(lambda n: Person().email())
    photo_url = 'https://ridesharing-photos.com/photo1.jpg'
    phone_number = factory.Sequence(
        lambda n: parse_phone_number('+7 (950) 000-00-00')
    )
    password = '12345'


class UserFactory(UserFactoryNoID):
    id = factory.Sequence(lambda n: n + 1)
