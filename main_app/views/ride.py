import operator
from datetime import datetime
from operator import attrgetter

from flask import jsonify, request
from flask_login import login_required, current_user
from geopy.distance import great_circle
from sqlalchemy.exc import IntegrityError

from app import db
from main_app.model import Ride, Organization, User, JoinRideRequest
from main_app.schemas import RideSchema, CreateRideSchema, \
    FindBestRidesSchema, RideJsonSchema, IdSchema, UserJsonSchema, JoinRideJsonSchema
from main_app.views import api
from main_app.responses import SwaggerResponses, build_error
from main_app.controller import validate_params_with_schema, format_time, validate_all
from main_app.views.user_and_driver import _get_user_info
from main_app.exceptions.custom import NotInOrganization, NotCarOwner, \
    RideNotActive, NoFreeSeats, CreatorCannotJoin, RequestAlreadySent

MAX_RIDES_IN_HISTORY = 10


def dump_rides(rides):
    ride_schema = RideSchema(many=True)
    response = ride_schema.dump(rides)
    for x in response:
        x['host_driver_info'] = _get_user_info(x['host_driver_id'])
    # Форматируем время
    response = format_time(response)
    return response


@api.route('/ride/active', methods=['GET'])
def active_rides():
    return jsonify(RideJsonSchema(only=(
        'id', 'free_seats',
        'submit_datetime', 'host',
        'price', 'car', 'stop_address',
        'host_answer', 'decline_reason'
    ), many=True).dump(filter(attrgetter('is_active'), current_user.all_rides)))


@api.route('/ride', methods=['PUT'])
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


@api.route('/get_all_rides', methods=['GET'])
@login_required
def get_all_rides():
    rides = db.session.query(Ride).filter_by(is_available=True).all()
    return jsonify(dump_rides(rides)[::-1])


@api.route('/get_my_finished_rides', methods=['GET'])
@login_required
def get_my_finished_rides():
    # Все законченнные, которые ты хостил
    rides = db.session.query(Ride).filter(Ride.is_finished).\
        filter(Ride.host_driver_id == current_user.id).limit(MAX_RIDES_IN_HISTORY).all()
    # Все законченные, в которых ты был пассажиром
    rides.extend([x for x in current_user.all_rides if x.is_finished])
    return jsonify(dump_rides(rides))


# TODO: tests
@api.route('/create_ride', methods=['POST'])
@login_required
def create_ride():
    data = request.get_json()
    response = SwaggerResponses.RIDE_ID
    # 1. Валидация параметров
    errors = validate_all([validate_params_with_schema(CreateRideSchema(), data)])
    if errors:
        return errors
    user_id = current_user.id
    # 2. Пользователь должен быть водителем
    if not db.session.query(User).filter_by(id=user_id).first():
        error = build_error(SwaggerResponses.IS_NOT_DRIVER, user_id)
        return jsonify(error), 401
    # 3. Организация должна существовать
    organization = db.session.query(Organization).\
        filter_by(id=data['start_organization_id']).first()
    if not organization:
        error = build_error(SwaggerResponses.INVALID_ORGANIZATION_ID, data['start_organization_id'])
        return jsonify(error), 400
    ride = Ride(
        start_organization_id=organization.id,
        start_organization=organization,
        cost=data.get('cost'),
        stop_latitude=data['stop_latitude'],
        stop_longitude=data['stop_longitude'],
        stop_address=data.get('stop_address'),
        start_time=data.get('start_time'),
        total_seats=data.get('total_seats'),
        description=data.get('description'),
        host_driver_id=user_id,
        car_id=data['car_id']
    )
    db.session.add(ride)
    db.session.commit()
    response['ride_id'] = ride.id
    return jsonify(response), 200


@api.route('/find_best_rides', methods=['POST'])
@login_required
def find_best_rides():
    """
    Здесь как раз будут все данные: откуда, id организации отправления, куда -- геокоординаты

    :return:
    """
    data = request.get_json()
    errors = validate_all([validate_params_with_schema(FindBestRidesSchema(), data)])
    if errors:
        return errors
    start_organization_id = data['start_organization_id']
    destination_gps = (data['destination_latitude'], data['destination_longitude'])
    m_distance = data.get('max_destination_distance_km', 2)
    matching_results = _find_best_rides(start_organization_id, destination_gps,
                                        max_destination_distance_km=m_distance)
    response = matching_results
    return jsonify(response), 200


@api.route('/get_ride_info', methods=['GET'])
@login_required
def get_ride_info():
    data = request.args
    ride_schema = RideSchema()
    id = data.get('ride_id')
    # TODO: validation should be in schemas
    try:
        id = int(id)
    except ValueError:
        error = build_error(SwaggerResponses.INVALID_RIDE_WITH_ID, id)
        return jsonify(error), 400
    ride = db.session.query(Ride).filter_by(id=id).first()
    response = ride_schema.dump(ride)
    response = format_time([response])[0]
    # Дополнительные поля, не вошедшие в схему
    # TODO: мб как-то дополнить схему?
    response['host_driver_info'] = _get_user_info(ride.host_driver_id, include_organizations=False)
    response['seats_available'] = ride.total_seats - len(ride.passengers)
    return jsonify(response), 200


@api.route('/finish_ride', methods=['POST'])
@login_required
def finish_ride():
    data = request.get_json()
    ride_id = data.get('ride_id')
    if not ride_id:
        error = build_error(SwaggerResponses.INVALID_RIDE_WITH_ID, ride_id)
        return jsonify(error), 400
    # TODO: validation should be in schemas
    try:
        ride_id = int(ride_id)
    except TypeError:
        error = build_error(SwaggerResponses.INVALID_RIDE_WITH_ID, ride_id)
        return jsonify(error), 400
    ride = db.session.query(Ride).filter_by(id=ride_id).first()
    if ride is None:
        error = build_error(SwaggerResponses.INVALID_RIDE_WITH_ID, ride_id)
        return jsonify(error), 400
    if ride.host_driver_id != current_user.id:
        error = build_error(SwaggerResponses.NO_PERMISSION_FOR_USER, current_user.id)
        return jsonify(error), 400
    # Нельзя завершать поездки из будущего
    if ride.start_time > datetime.now():
        error = build_error(SwaggerResponses.RIDE_NOT_STARTED, ride_id)
        return jsonify(error), 400
    # is_finished -- только для того, чтобы отделить историю
    ride.is_finished = True
    # is_available -- более общий флаг. По нему и стоит судить, доступна ли поездка.
    ride.is_available = False
    db.session.commit()
    return jsonify(ride.id), 200


@api.route('/leave_ride', methods=['POST'])
@login_required
def leave_ride():
    data = request.get_json()
    ride_id = data.get('ride_id')
    if not ride_id:
        error = build_error(SwaggerResponses.INVALID_RIDE_WITH_ID, ride_id)
        return jsonify(error), 400
    # Мы сразу отбираем те поездки, которые не закончены
    ride = db.session.query(Ride).filter_by(id=ride_id).\
        filter_by(is_finished=False).first()
    # Если никаких таких поездок не нашлось
    if not ride:
        error = build_error(SwaggerResponses.INVALID_RIDE_WITH_ID, ride_id)
        return jsonify(error), 400
    # Иначе, убираем пользователя из поездки
    if current_user not in ride.passengers:
        error = build_error(SwaggerResponses.ERROR_USER_NOT_IN_RIDE, ride_id)
        return jsonify(error), 400
    ride.passengers.remove(current_user)
    # Обновим поездку
    ride.is_available = True
    db.session.commit()
    response = {'ride_id': ride_id}
    return jsonify(response), 200


@api.route('/get_my_rides', methods=['GET'])
@login_required
def get_my_rides():
    # Все, которые ты хостил
    rides = db.session.query(Ride).filter(
        (Ride.host_driver_id == current_user.id) & (not Ride.is_finished))\
        .all()
    # Все, в которых ты был пассажиром
    rides.extend([x for x in current_user.all_rides if not x.is_finished])
    return jsonify(dump_rides(rides))


# TODO: for now, `organizations` is ignored
# TODO: Optimization! Don't take all rides, use more filters
def _find_best_rides(start_organization_id, destination_gps, max_destination_distance_km=2):
    # Get all rides starting from exact organization and are available
    ride_schema = RideSchema()
    all_rides = db.session.query(Ride)\
        .filter_by(start_organization_id=start_organization_id)\
        .filter_by(is_available=True).filter_by(is_mine=False).all()
    # For each ride, find distance to `gps`
    # We make top based on  destination point
    result_top = []
    for ride in all_rides:
        distance = great_circle(
            (ride.stop_latitude, ride.stop_longitude),
            destination_gps
        ).kilometers
        if distance >= max_destination_distance_km:
            continue
        ride_info = ride_schema.dump(ride)
        ride_info['host_driver_info'] = _get_user_info(ride.host_driver_id)
        ride_info = format_time([ride_info])[0]
        result_top.append((ride_info, distance))
    result_top.sort(key=operator.itemgetter(1))
    return result_top
