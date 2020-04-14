from flask_login import UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import validates
from main_app.misc import reverse_geocoding_blocking
from datetime import datetime

from main_app.search import query_index, add_to_index, remove_from_index
from app import db
from settings import MAX_EMAIL_LENGTH, MAX_NAME_LENGTH, MAX_SURNAME_LENGTH, MAX_URL_LENGTH

association_user_ride = db.Table(
    'association_user_ride', db.metadata,
    db.Column('left_id', db.Integer, db.ForeignKey(f'user.id')),
    db.Column('right_id', db.Integer, db.ForeignKey('ride.id'))
)

association_user_organization = db.Table(
    'association_user_organization', db.metadata,
    db.Column('left_id', db.Integer, db.ForeignKey('user.id', ondelete='cascade')),
    db.Column('right_id', db.Integer, db.ForeignKey('organization.id', ondelete='cascade'))
)


class SearchableMixin:
    @classmethod
    def search(cls, expression, page, per_page):
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return cls.query.filter_by(id=0), 0
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        if not when:    # workaround for empty list crash
            return cls.query.filter(cls.id.in_(ids)), total
        return cls.query.filter(cls.id.in_(ids)).order_by(
            db.case(when, value=cls.id)), total

    @classmethod
    def before_commit(cls, session):
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls):
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)


db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)


class RatingMixin:
    """
    Mixin for rating calculation. Class should have `reviews` field.
    """
    @hybrid_property
    def rating(self):
        if not self.reviews:
            return 0.
        return sum([x.rate for x in self.reviews])/len(self.reviews)


class User(UserMixin, RatingMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(MAX_NAME_LENGTH), nullable=False)
    last_name = db.Column(db.String(MAX_SURNAME_LENGTH), nullable=False)
    email = db.Column(db.String(MAX_EMAIL_LENGTH), nullable=False, unique=True)
    photo_url = db.Column(db.String(MAX_URL_LENGTH))
    phone_number = db.Column(db.String(20), server_default='+71111111111', nullable=False)
    _password_hash = db.Column(db.String(94), nullable=False)

    @hybrid_property
    def password(self):
        return self._password_hash

    @password.setter
    def password(self, value):
        self._password_hash = generate_password_hash(value)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class JoinRideRequest(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, primary_key=True)
    user = db.relationship('User', backref='join_requests')
    ride_id = db.Column(db.Integer, db.ForeignKey('ride.id'), nullable=False, primary_key=True)
    ride = db.relationship('Ride', backref='join_requests')
    # 0 - no answer, 1 - accepted, -1 - declined
    status = db.Column(db.Integer, nullable=False, server_default='0')
    decline_reason = db.Column(db.String(200))


class Organization(SearchableMixin, db.Model):
    __searchable__ = ['name', 'address']
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(600), nullable=False, server_default='undefined')
    description = db.Column(db.String(600))
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, server_default='1')
    creator = db.relationship('User')
    control_question = db.Column(db.String(400), nullable=False, server_default='undefined')
    control_answer = db.Column(db.String(200), nullable=False, server_default='undefined')
    users = db.relationship('User', secondary=association_user_organization,
                            backref='organizations',
                            cascade='all, delete',
                            passive_deletes=True
                            )
    photo_url = db.Column(db.String(MAX_URL_LENGTH))

    @validates('creator')
    def ensure_is_member(self, key, value):
        if value not in self.users:
            self.users.append(value)
        return value

    @hybrid_property
    def last_ride_datetime(self):
        return max([x.submit_datetime for x in self.is_start_for]) if self.is_start_for else '-'

    @hybrid_property
    def total_members(self):
        return len(self.users)

    @hybrid_property
    def total_drivers(self):
        return sum([len(user.cars) > 0 for user in self.users])

    @hybrid_property
    def min_ride_cost(self):
        return min([x.price for x in self.is_start_for]) if self.is_start_for else '-'

    @hybrid_property
    def max_ride_cost(self):
        return max([x.price for x in self.is_start_for]) if self.is_start_for else '-'


class Ride(RatingMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)

    start_organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    start_organization = db.relationship(
        'Organization', backref='is_start_for', foreign_keys=[start_organization_id])

    stop_latitude = db.Column(db.Float, nullable=False)
    stop_longitude = db.Column(db.Float, nullable=False)
    submit_datetime = db.Column(db.DateTime, server_default=datetime.now().isoformat())
    start_datetime = db.Column(db.DateTime, nullable=False)
    stop_datetime = db.Column(db.DateTime)

    total_seats = db.Column(db.Integer, server_default='4', nullable=False)
    host_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    host = db.relationship('User', backref='hosted_rides')
    passengers = db.relationship('User', secondary=association_user_ride, backref='all_rides')

    is_active = db.Column(db.Boolean, nullable=False, server_default='true')

    price = db.Column(db.Float, nullable=False, server_default='0')
    car_id = db.Column(db.Integer, db.ForeignKey('car.id'), nullable=False, server_default='2')
    car = db.relationship('Car')
    description = db.Column(db.String(600))

    @hybrid_property
    def free_seats(self):
        return self.total_seats - len(self.passengers)

    @hybrid_property
    def stop_address(self):
        return reverse_geocoding_blocking(
            latitude=self.stop_latitude, longitude=self.stop_longitude
        )['address']

    @hybrid_property
    def is_mine(self):
        return self.host == current_user

    @hybrid_property
    def host_answer(self):
        for request in self.join_requests:
            if request.user == current_user:
                return {1: 'ACCEPTED', 0: 'NO ANSWER', -1: 'DECLINED'}.get(request.status)

    @hybrid_property
    def decline_reason(self):
        for request in self.join_requests:
            if request.user == current_user:
                return request.decline_reason or ''


class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(100), nullable=False)
    registry_number = db.Column(db.String(20), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    owner = db.relationship('User', backref='cars')


class FeedbackMixin:

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    @declared_attr
    def voter_id(cls):
        return db.Column(db.Integer, db.ForeignKey(f'user.id'), nullable=False, server_default='1')

    @declared_attr
    def voter(cls):
        return db.relationship(User, backref=f'{cls.__tablename__}_left',
                               foreign_keys=[cls.voter_id])

    id = db.Column(db.Integer, primary_key=True)
    rate = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(600))


class UserFeedback(FeedbackMixin, db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship(User, backref='reviews', foreign_keys=[user_id, ])


class RideFeedback(FeedbackMixin, db.Model):
    ride_id = db.Column(db.Integer, db.ForeignKey('ride.id'), nullable=False)
    ride = db.relationship(Ride, backref='reviews')
