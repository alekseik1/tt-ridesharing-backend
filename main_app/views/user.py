from flask import jsonify
from flask_login import login_required, current_user

from app import db
from main_app.model import Driver
from main_app.schemas import UserSchema
from main_app.views import api


@api.route('/get_user_info', methods=['GET'])
@login_required
def get_user_info():
    user_schema = UserSchema()
    response = user_schema.dump(current_user)
    return jsonify(response), 200


@api.route('/am_i_driver', methods=['GET'])
@login_required
def am_i_driver():
    driver = db.session.query(Driver).filter_by(id=current_user.id).first()
    if driver:
        return jsonify(is_driver=True), 200
    return jsonify(is_driver=False)


