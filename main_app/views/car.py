from flask import jsonify, request
from flask_login import login_required, current_user

from main_app.schemas import CarSchema, CarPermissiveSchema, IdSchema
from app import db
from main_app.exceptions.custom import InsufficientPermissions
from main_app.views import api


@api.route('/car', methods=['GET', 'POST', 'PUT'])
@login_required
def car():
    if request.method == 'GET':
        # Only own cars
        return jsonify(CarSchema(many=True).dump(current_user.cars))
    if request.method == 'POST':
        car = CarPermissiveSchema().load(request.json)
        # If not found in DB, abort
        if car.owner != current_user:
            raise InsufficientPermissions()
        # Update car values
        db.session.add(car)
        db.session.commit()
        return IdSchema().dump(car)
    if request.method == 'PUT':
        car = CarSchema(exclude=('id', )).load(request.json)
        car.owner = current_user
        db.session.add(car)
        db.session.commit()
        return IdSchema().dump(car)
