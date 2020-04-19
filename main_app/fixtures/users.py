import factory.fuzzy
from mimesis import Person, locales

from app import db
from main_app.controller import parse_phone_number
from main_app.model import User, UserFeedback
from main_app.fixtures.cars import CarFactory


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):

    class Meta:
        model = User
        sqlalchemy_session = db.session
    first_name = factory.Sequence(lambda n: Person(locale=locales.RU, seed=n).name())
    last_name = factory.Sequence(lambda n: Person(locale=locales.RU, seed=n).surname())
    email = factory.Sequence(lambda n: f'user_{n+1}@gmail.com')
    photo_url = 'https://ridesharing-photos.com/photo1.jpg'
    phone_number = factory.Sequence(
        lambda n: parse_phone_number('+7 (950) {}{}{}-{}{}-{}{}'.format(
            *[factory.fuzzy.random.randgen.randint(0, 9) for _ in range(7)]))
    )
    password = '12345'
    cars = factory.RelatedFactoryList(CarFactory, 'owner', size=1)


class UserFeedbackFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = UserFeedback
        sqlalchemy_session = db.session
        exclude = ['id', ]
    rate = factory.fuzzy.FuzzyInteger(1, 10)
    description = factory.Sequence(lambda n: f'feedback_{n}')

    @factory.post_generation
    def user(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.user = extracted
        else:
            raise Exception(f'You should provide `user`')
