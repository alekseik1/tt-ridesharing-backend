from datetime import datetime
from operator import attrgetter

from flask import jsonify, request
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

from app import db
from main_app.model import Ride, Organization, JoinRideRequest
from main_app.schemas import \
    RideJsonSchema, IdSchema, UserJsonSchema, \
    JoinRideJsonSchema, RideSearchSchema
from main_app.views import api
from main_app.exceptions.custom import NotInOrganization, NotCarOwner, \
    RideNotActive, NoFreeSeats, CreatorCannotJoin, RequestAlreadySent, InsufficientPermissions
from main_app.misc import get_distance

MAX_RIDES_IN_HISTORY = 10


@api.route('/ride/active', methods=['GET'])
@login_required
def active_rides():
    return jsonify(RideJsonSchema(only=(
        'id', 'free_seats',
        'submit_datetime', 'host',
        'price', 'car', 'stop_address',
        'host_answer', 'decline_reason'
    ), many=True).dump(filter(attrgetter('is_active'), current_user.all_rides)))


@api.route('/ride/match', methods=['POST'])
@login_required
def match_ride():
    data = RideSearchSchema().load(request.json)
    org = db.session.query(Organization).filter_by(id=data['id']).first()
    if not org:
        raise InsufficientPermissions()
    if org not in current_user.organizations:
        raise NotInOrganization()
    latitude, longitude = data['gps']['latitude'], data['gps']['longitude']

    # match ride
    all_rides = db.session.query(Ride).\
        filter(Ride.start_organization_id == org.id).\
        filter(Ride.is_active).all()
    ranged_rides = sorted(
        all_rides,
        key=lambda ride: get_distance(
            (ride.stop_latitude, ride.stop_longitude),
            (latitude, longitude))
    )
    return jsonify(RideJsonSchema(only=(
        'id', 'car', 'submit_datetime',
        'price', 'host', 'free_seats',
        'passengers', 'stop_address',
        'start_organization_address',
    ), many=True).dump(ranged_rides))


@api.route('/ride', methods=['PUT'])
@login_required
def ride():
    if request.method == 'PUT':
        ride = RideJsonSchema(only=(
            'car_id', 'start_organization_id',
            'stop_latitude', 'stop_longitude',
            'total_seats', 'price', 'description'
        )).load(request.json)
        ride.host = current_user
        if ride.start_organization_id not in [x.id for x in current_user.organizations]:
            raise NotInOrganization()
        if ride.car_id not in [car.id for car in current_user.cars]:
            raise NotCarOwner()
        ride.submit_datetime = datetime.now().isoformat()
        db.session.add(ride)
        db.session.commit()
        return IdSchema().dump(ride)


@api.route('/ride/passengers', methods=['GET'])
@login_required
def passengers():
    return jsonify(
        UserJsonSchema(only=(
            'first_name', 'last_name', 'photo_url', 'rating', 'id'
        ), many=True).dump(
            getattr(
                db.session.query(Ride).filter_by(**IdSchema().load(request.args)).first(),
                'passengers', [])
        )
    )


@api.route('/ride/join', methods=['POST'])
@login_required
def ride_join():
    ride = RideJsonSchema(only=('id', )).load(request.json)
    if not ride.is_active:
        raise RideNotActive()
    if ride.start_organization not in current_user.organizations:
        raise NotInOrganization()
    if ride.free_seats < 1:
        raise NoFreeSeats()
    if ride.is_mine:
        raise CreatorCannotJoin()
    join_request = JoinRideRequest(user_id=current_user.id, ride_id=ride.id)
    try:
        db.session.add(join_request)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise RequestAlreadySent()
    return JoinRideJsonSchema(exclude=('status',)).dump(join_request)
