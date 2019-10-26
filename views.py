from flask import request, url_for, redirect, flash, Blueprint, jsonify
from flask_login import current_user, login_user, login_required, logout_user
from model import RegisterUserSchema, User, RegisterDriverSchema, Driver, Ride, Organization, \
    OrganizationSchema, UserSchema, CreateRideSchema, JoinRideSchema, FindBestRidesSchema, OrganizationIDSchema
from sqlalchemy.exc import IntegrityError
from utils.exceptions import InvalidData, ResponseExamples
from utils.misc import validate_is_in_db, validate_params_with_schema, validate_is_authorized_with_id, validate_all
from app import db
from utils.ride_matcher import _find_best_rides

api = Blueprint('api', __name__)
# TODO: перенести это в конфиг
MAX_ORGANIZATIONS_PER_USER = 5


@api.route('/', methods=['GET', 'POST'])
def root():
    return redirect(url_for('.'+index.__name__))


@api.route('/index')
def index():
    return 'Welcome to our service!'


@api.route('/register_user', methods=['POST'])
def register_user():
    data = request.get_json()
    errors = validate_all([validate_params_with_schema(RegisterUserSchema(), data)])
    if errors:
        return errors
    user = User(first_name=data['first_name'], last_name=data['last_name'], email=data['email'])
    user.set_password(password=data['password'])
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError as e:
        error = ResponseExamples.EMAIL_IS_BUSY
        error['value'] = data['email']
        return jsonify(error), 400
    return jsonify(user_id=user.id)


@api.route('/register_driver', methods=['POST'])
@login_required
def register_driver():
    data = request.get_json()
    user_id = data.get('user_id')
    errors = validate_all([
        validate_params_with_schema(RegisterDriverSchema(), data=data),
        validate_is_in_db(db, user_id),
        validate_is_authorized_with_id(user_id, current_user),
    ])
    if errors:
        return errors
    driver = Driver(
        id=int(user_id),
        passport_1=data['passport_url_1'],
        passport_2=data['passport_url_2'],
        passport_selfie=data['passport_url_selfie'],
        driver_license_1=data['license_1'],
        driver_license_2=data['license_2']
    )
    db.session.add(driver)
    try:
        db.session.commit()
    except Exception as e:
        error = ResponseExamples.UNHANDLED_ERROR
        error['value'] = e.args
        return jsonify(error), 400
    return jsonify(user_id=driver.id)


@api.route('/login', methods=['POST'])
def login():
    # Check if current user is authenticated
    if current_user.is_authenticated:
        error = ResponseExamples.ALREADY_LOGGED_IN
        return jsonify(error), 400
    data = request.get_json()
    login = data.get('login')
    password = data.get('password')
    # We login only via email for now
    user = User.query.filter_by(email=login).first()
    if user is None or not user.check_password(password):
        error = ResponseExamples.INCORRECT_LOGIN
        return jsonify(error), 400
    login_user(user, remember=True)
    response = ResponseExamples.USER_ID
    response['user_id'] = user.id
    return jsonify(response), 200


@api.route('/logout', methods=['POST'])
def logout():
    # Check if current user is authenticated
    if not current_user.is_authenticated:
        error = ResponseExamples.AUTHORIZATION_REQUIRED
        return jsonify(error), 400
    logout_user()
    return '', 200


@api.route('/get_user_info', methods=['GET'])
@login_required
def get_user_info():
    response = ResponseExamples.USER_INFO
    response['user_id'] = current_user.id
    response['first_name'] = current_user.first_name
    response['last_name'] = current_user.last_name
    response['email'] = current_user.email
    response['photo_url'] = current_user.photo
    return jsonify(response), 200


@api.route('/get_all_rides', methods=['GET'])
@login_required
def get_all_rides():
    rides = db.session.query(Ride).filter_by(is_available=True).all()
    response = []
    organization_schema = OrganizationSchema()
    user_schema = UserSchema(many=True)
    for ride in rides:
        ride_info = ResponseExamples.RIDE_INFO
        start_organization = db.session.query(Organization).filter_by(id=ride.start_organization_id).first()
        ride_info['start_organization'] = organization_schema.dump(start_organization)
        ride_info['stop_latitude'] = ride.stop_latitude
        ride_info['stop_longitude'] = ride.stop_longitude
        ride_info['start_time'] = str(ride.start_time)
        ride_info['host_driver_id'] = ride.host_driver_id
        ride_info['estimated_time'] = ride.estimated_time
        ride_info['passengers'] = user_schema.dump(ride.passengers, many=True)
        response.append(ride_info)
    return jsonify(response), 200


# TODO: tests
@api.route('/create_ride', methods=['POST'])
@login_required
def create_ride():
    data = request.get_json()
    response = ResponseExamples.RIDE_ID
    # 1. Валидация параметров
    errors = validate_all([validate_params_with_schema(CreateRideSchema(), data)])
    if errors:
        return errors
    user_id = data.get('host_driver_id')
    # 2. Пользователь должен быть водителем
    if not db.session.query(Driver).filter_by(id=user_id).first():
        error = ResponseExamples.IS_NOT_DRIVER
        error['value'] = user_id
        return jsonify(error), 401
    # 3. Организация должна существовать
    organization = db.session.query(Organization).filter_by(id=data['start_organization_id']).first()
    if not organization:
        error = ResponseExamples.INVALID_ORGANIZATION_ID
        error['value'] = data['start_organization_id']
        return jsonify(error), 400
    ride = Ride(
        start_organization_id=organization.id,
        start_organization=organization,
        stop_latitude=data['stop_latitude'],
        stop_longitude=data['stop_longitude'],
        start_time=data.get('start_time'),
        host_driver_id=user_id
    )
    db.session.add(ride)
    db.session.commit()
    response['ride_id'] = ride.id
    return jsonify(response), 200


@api.route('/get_all_organizations', methods=['GET'])
@login_required
def get_all_organizations():
    organization_schema = OrganizationSchema(many=True)
    result = organization_schema.dump(db.session.query(Organization).all(), many=True)
    return jsonify(result), 200


# TODO: better tests
@api.route('/join_ride', methods=['POST'])
@login_required
def join_ride():
    data = request.get_json()
    # 1. Валидация параметров
    errors = validate_all([validate_params_with_schema(JoinRideSchema(), data)])
    if errors:
        return errors
    ride_id = data['ride_id']
    # 2. Поездка должна существовать
    ride = db.session.query(Ride).filter_by(id=ride_id).first()
    if not ride:
        error = ResponseExamples.INVALID_RIDE_WITH_ID
        error['value'] = ride_id
        return jsonify(error), 400
    # 3. Вроде, все ок. Можно добавлять в поездку
    ride.passengers.append(current_user)
    db.session.commit()
    response = ResponseExamples.RIDE_ID
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
    matching_results = _find_best_rides(start_organization_id, destination_gps)
    response = ResponseExamples.MATCHING_RESULTS
    response['top'] = matching_results
    return jsonify(response), 200


@api.route('/join_organization', methods=['POST'])
@login_required
def join_organization():
    """
    {'organization_id": 34}

    :return:
    """
    data = request.get_json()
    errors = validate_all([validate_params_with_schema(OrganizationIDSchema(), data)])
    if errors:
        return errors
    if len(current_user.organizations) >= MAX_ORGANIZATIONS_PER_USER:
        error = ResponseExamples.ORGANIZATION_LIMIT
        return jsonify(error), 400
    data_organization_id = data['organization_id']
    organization = db.session.query(Organization).filter_by(id=data_organization_id).first()
    if not organization:
        error = ResponseExamples.INVALID_ORGANIZATION_ID
        error['value'] = data_organization_id
        return jsonify(error), 400
    current_user.organizations.append(organization)
    db.session.commit()
    # TODO: сделать его
    response = ResponseExamples.ORGANIZATION_ID
    response['organization_id'] = organization.id
    return jsonify(response), 200


@api.route('/leave_organization', methods=['POST'])
@login_required
def leave_organization():
    """
    {'organization_id': 36}

    :return:
    """
    data = request.get_json()
    errors = validate_all([validate_params_with_schema(OrganizationIDSchema(), data)])
    if errors:
        return errors
    organization_id = data['organization_id']
    organization_to_leave = db.session.query(Organization).filter_by(id=organization_id).first()
    if not organization_to_leave:
        error = ResponseExamples.INVALID_ORGANIZATION_ID
        error['value'] = organization_id
        return jsonify(organization_id), 400
    if organization_to_leave not in current_user.organizations:
        error = ResponseExamples.ERROR_NOT_IN_ORGANIZATION
        error['value'] = organization_id
        return jsonify(error), 400
    current_user.organizations.remove(organization_to_leave)
    db.session.commit()
    response = ResponseExamples.ORGANIZATION_ID
    response['value'] = organization_id
    return jsonify(response), 200
