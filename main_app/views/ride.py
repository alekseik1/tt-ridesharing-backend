from datetime import datetime
from typing import List

from flask import jsonify, request
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

from app import db
from main_app.model import Ride, Organization, JoinRideRequest, RideFeedback
from main_app.schemas import \
    RideJsonSchema, IdSchema, UserJsonSchema, \
    JoinRideJsonSchema, RideSearchSchema, RideFeedbackSchema, STANDART_RIDE_INFO
from main_app.views import api
from main_app.exceptions.custom import NotInOrganization, NotCarOwner, \
    RideNotActive, NoFreeSeats, CreatorCannotJoin, RequestAlreadySent, InsufficientPermissions, \
    NotInRide, NotForOwner, RideNotFinished, AlreadyDecided
from main_app.misc import get_distance

MAX_RIDES_IN_HISTORY = 10


@api.route('/ride/active', methods=['GET'])
@login_required
def active_rides():
    # TODO: move logic to SQL-query, not pythonic `filter`
    requests_to_active_rides = filter(
        lambda request: request.ride.is_active,
        current_user.join_requests)
    return jsonify(RideJsonSchema(only=(
        STANDART_RIDE_INFO + ['host_answer', 'organization_address']
    ), many=True).dump([request.ride for request in requests_to_active_rides]))


@api.route('/ride/match', methods=['GET'])
@login_required
def match_ride():
    data = RideSearchSchema().load(request.args)
    org = db.session.query(Organization).filter_by(id=data['id']).first()
    if not org:
        raise InsufficientPermissions()
    if org not in current_user.organizations:
        raise NotInOrganization()
    latitude, longitude = data['latitude'], data['longitude']
    from_organization = data['from_organization']

    # match ride
    all_rides = db.session.query(Ride).\
        filter(Ride.organization_id == org.id).\
        filter(Ride.from_organization == from_organization).\
        filter(Ride.is_active).all()
    ranged_rides = sorted(
        all_rides,
        key=lambda ride: get_distance(
            (ride.latitude, ride.longitude),
            (latitude, longitude))
    )
    return jsonify(RideJsonSchema(only=(
        'id', 'car', 'submit_datetime', 'start_datetime',
        'price', 'host', 'free_seats',
        'passengers',
        'organization_address', 'host_answer',
        'latitude', 'longitude', 'address',
    ), many=True).dump(ranged_rides))


@api.route('/ride', methods=['PUT'])
@login_required
def ride():
    if request.method == 'PUT':
        ride = RideJsonSchema(only=(
            'car_id', 'organization_id',
            'latitude', 'longitude', 'from_organization',
            'total_seats', 'price', 'description', 'start_datetime'
        )).load(request.json)
        ride.host = current_user
        if ride.organization_id not in [x.id for x in current_user.organizations]:
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
    if ride.organization not in current_user.organizations:
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
    return JoinRideJsonSchema(exclude=('status', 'user', )).dump(join_request)


@api.route('/ride/history', methods=['GET'])
@login_required
def my_rides_history():
    all_requests = db.session.query(JoinRideRequest).filter(
        JoinRideRequest.user == current_user
    ).all()     # type: List[JoinRideRequest]
    return jsonify(RideJsonSchema(many=True, only=(
        'id', 'host', 'organization_name', 'address',
        'submit_datetime', 'start_datetime', 'stop_datetime',
        'price'
    )).dump([x.ride for x in all_requests if not x.ride.is_active]))


@api.route('/ride/rate', methods=['PUT'])
@login_required
def rate_ride():
    review = RideFeedbackSchema().load(request.json)    # type: RideFeedback
    if current_user not in review.ride.passengers:
        raise NotInRide()
    if current_user == review.ride.host:
        raise NotForOwner()
    if review.ride.is_active:
        raise RideNotFinished()
    review.voter = current_user
    db.session.add(review)
    db.session.commit()
    return RideFeedbackSchema(only=('id', )).dump(review)


@api.route('/ride/requests', methods=['GET'])
@login_required
def ride_requests():
    result = db.session.query(JoinRideRequest).filter(
        JoinRideRequest.ride_id.in_([x.id for x in current_user.hosted_rides])
    ).filter_by(status=0).all()     # 0 - not decided
    return jsonify(JoinRideJsonSchema(many=True, only=(
        'ride_id', 'user',
    )).dump(result))


@api.route('/ride/hosted', methods=['GET'])
@login_required
def my_hosted_rides():
    return jsonify(RideJsonSchema(many=True, only=STANDART_RIDE_INFO).dump(
        filter(lambda ride: ride.is_active, current_user.hosted_rides)))


def deactivate_ride(ride):
    if not ride.is_mine:
        raise InsufficientPermissions()
    if not ride.is_active:
        raise RideNotActive()
    ride.is_active = False
    ride.stop_datetime = datetime.now().isoformat()
    db.session.commit()


@api.route('/ride/finish', methods=['POST'])
@login_required
def finish_ride():
    ride = RideJsonSchema(only=('id', )).load(request.json)
    deactivate_ride(ride)
    # Mark all undecided requests as 'DECLINED'
    for join_request in db.session.query(JoinRideRequest).\
            filter_by(status=0).filter_by(ride_id=ride.id).all():
        join_request.status = -1
    db.session.commit()
    return RideJsonSchema(only=('id', )).dump(ride)


@api.route('/ride/cancel', methods=['POST'])
@login_required
def cancel_ride():
    ride = RideJsonSchema(only=('id', )).load(request.json)
    deactivate_ride(ride)
    # Remove all passengers
    ride.passengers = []
    # Mark all join requests as `DECLINED`
    for join_request in db.session.query(JoinRideRequest).filter_by(ride_id=ride.id).all():
        join_request.status = -1
    db.session.commit()
    return RideJsonSchema(only=('id', )).dump(ride)


def process_join_request(join_request: JoinRideRequest, action: str):
    if join_request.user is None or join_request.ride is None:
        # Not found in DB
        raise InsufficientPermissions()
    if join_request.ride.host != current_user:
        raise InsufficientPermissions()
    if join_request.status != 0:
        raise AlreadyDecided()
    if action == 'ACCEPT':
        if join_request.ride.free_seats < 1:
            raise NoFreeSeats()
        join_request.status = 1
    elif action == 'DECLINE':
        join_request.status = -1
    db.session.commit()


@api.route('/ride/request/accept', methods=['POST'])
@login_required
def accept_request():
    join_request = JoinRideJsonSchema(only=('user_id', 'ride_id')).load(request.json)
    process_join_request(join_request, 'ACCEPT')
    # Add to passengers
    join_request.ride.passengers.append(join_request.user)
    db.session.commit()
    return 'ok'


@api.route('/ride/request/decline', methods=['POST'])
@login_required
def decline_request():
    join_request = JoinRideJsonSchema(
        only=('user_id', 'ride_id', 'decline_reason')).load(request.json)
    process_join_request(join_request, 'DECLINE')
    return 'ok'
