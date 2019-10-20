from flask import request, url_for, redirect, flash, Blueprint, jsonify
from flask_login import current_user, login_user, login_required, logout_user
from model import RegisterUserSchema, User, RegisterDriverSchema, Driver, Ride, Organization, \
    OrganizationSchema, UserSchema, CreateRideSchema
from sqlalchemy.exc import IntegrityError
from utils.exceptions import InvalidData, ResponseExamples
from utils.misc import validate_is_in_db, validate_params_with_schema, validate_is_authorized_with_id, validate_all
from app import db

api = Blueprint('api', __name__)


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
        return error, 400
    data = request.get_json()
    login = data.get('login')
    password = data.get('password')
    # We login only via email for now
    user = User.query.filter_by(email=login).first()
    if user is None or not user.check_password(password):
        error = ResponseExamples.INCORRECT_LOGIN
        return error, 400
    login_user(user, remember=True)
    response = ResponseExamples.USER_ID
    response['user_id'] = user.id
    return response, 200


@api.route('/logout', methods=['POST'])
def logout():
    # Check if current user is authenticated
    if not current_user.is_authenticated:
        error = ResponseExamples.AUTHORIZATION_REQUIRED
        return error, 400
    logout_user()
    return '', 200


@api.route('/get_user_data', methods=['GET'])
@login_required
def get_user_data():
    data = request.args
    user = db.session.query(User).filter_by(email=data['email']).first()
    if user is None:
        error = ResponseExamples.INVALID_USER_WITH_EMAIL
        error['value'] = data['email']
        return jsonify(error), 400
    response = ResponseExamples.USER_INFO
    response['user_id'] = user.id
    response['first_name'] = user.first_name
    response['last_name'] = user.last_name
    response['email'] = user.email
    response['photo_url'] = user.photo
    return jsonify(response), 200


# TODO: tests
@api.route('/get_all_rides', methods=['GET'])
@login_required
def get_all_rides():
    rides = db.session.query(Ride).all()
    response = []
    organization_schema = OrganizationSchema()
    user_schema = UserSchema(many=True)
    for ride in rides:
        ride_info = ResponseExamples.RIDE_INFO
        start_organization = db.session.query(Organization).filter_by(id=ride.start_organization_id).first()
        stop_organization = db.session.query(Organization).filter_by(id=ride.stop_organization_id).first()
        ride_info['start_organization'] = organization_schema.dump(start_organization)
        ride_info['stop_organization'] = organization_schema.dump(stop_organization)
        ride_info['start_time'] = ride.start_time
        ride_info['host_driver_id'] = ride.host_driver_id
        ride_info['estimated_time'] = ride.estimated_time
        ride_info['passengers'] = user_schema.dump(ride.passengers)
        response.append(ride_info)
    return jsonify(response), 200


# TODO: tests
@api.route('/create_ride', methods=['POST'])
@login_required
def create_ride():
    data = request.get_json()
    # 1. Валидация параметров
    errors = validate_all([validate_params_with_schema(CreateRideSchema(), data)])
    if errors:
        return errors
    user_id = data.get('host_driver_id')
    # 2. Пользователь должен быть водителем
    if not db.session.query(Driver).filter_by(id=user_id).first():
        error = ResponseExamples.IS_NOT_DRIVER
        error['value'] = user_id
        return error, 401
    ride = Ride(
        start_organization_id=data.get('start_organization_id'),
        stop_organization_id=data.get('stop_organization_id'),
        start_time=data.get('start_time')
    )
    db.session.add(ride)
    db.session.commit()
    return jsonify({'ride_id': ride.id}), 200
