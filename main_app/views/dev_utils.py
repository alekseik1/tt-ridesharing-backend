from app import db
from flask import current_app
from main_app.views import api
from fill_db import fill_database


@api.route('/recreate_db', methods=['POST'])
def recreate_db():
    db.drop_all()
    fill_database(current_app)
    return ''
