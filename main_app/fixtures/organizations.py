import factory.fuzzy
from main_app.model import Organization
from app import db
from main_app.views.misc import reverse_geocoding_blocking


class OrganizationFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Organization
        sqlalchemy_session = db.session
        exclude = ['id', ]
    name = factory.Sequence(lambda n: f'organization_{n}')
    latitude = factory.fuzzy.FuzzyFloat(-20.0, +20.0)
    longitude = factory.fuzzy.FuzzyFloat(-20.0, +20.0)
    address = factory.lazy_attribute(lambda o:
        reverse_geocoding_blocking(latitude=o.latitude, longitude=o.longitude)['address']
    )
