from flask import jsonify, request
from flask_login import login_required, current_user

from main_app.schemas import CarSchema, RegisterCarForDriverSchema, IdSchema
from app import db
from main_app.model import Car, User
from main_app.exceptions.custom import InsufficientPermissions
from main_app.controller import validate_params_with_schema
from main_app.views import api


@api.route('/car', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def car():
    if request.method == 'GET':
        # Only own cars
        return jsonify(CarSchema(many=True).dump(current_user.cars))
    if request.method == 'POST':
        return {}
    if request.method == 'PUT':
        car = CarSchema(exclude=('id', )).load(request.json)
        car.owner = current_user
        db.session.add(car)
        db.session.commit()
        return IdSchema().dump(car)
    if request.method == 'DELETE':
        car = CarSchema(only=('id',)).load(request.json)
        if current_user != getattr(car, 'owner', -1):
            raise InsufficientPermissions()
        db.session.delete(car)
        db.session.commit()
        return ''


@api.route('/get_my_cars', methods=['GET'])
@login_required
def get_my_cars():
    car_schema = CarSchema(many=True)
    corresponding_driver = db.session.query(User).filter_by(id=current_user.id).first()
    return jsonify(car_schema.dump(corresponding_driver.cars))


def register_car(car_info):
    car = Car(**car_info)
    db.session.add(car)
    db.session.commit()
    return car


@api.route('/register_own_car', methods=['POST'])
@login_required
def register_car_for_driver():
    data = request.get_json()
    # Также валидирует на наличие водителя. Я начал писать нормально
    error = validate_params_with_schema(RegisterCarForDriverSchema(), data)
    if error:
        return error
    data['owner_id'] = current_user.id
    car = register_car(data)
    return jsonify(car_id=car.id), 200
