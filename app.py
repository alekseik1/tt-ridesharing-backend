import logging
import os
from datetime import datetime

from flask import Flask, jsonify
from flask_cors import CORS
from flask_login import LoginManager
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import Unauthorized

from instance.config import configs
from main_app.responses import SwaggerResponses

db = SQLAlchemy()
migrate = Migrate()
ma = Marshmallow()
login = LoginManager()


def create_app(config_name):
    app = Flask(__name__)

    # Take config from `config.py`
    config = configs.get(config_name)
    app.config.from_object(config)
    # Configure database
    app.config['SQLALCHEMY_DATABASE_URI'] = config.DB_URI
    app.secret_key = config.secret_key

    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)
    # Enable CORS for any ports, any origins
    CORS(app, supports_credentials=True)
    login.init_app(app)
    # register all Blueprints
    from main_app.views import auth, user_and_driver, organization, ride, car
    from main_app.views import api
    app.register_blueprint(api)

    from main_app.model import User
    @login.user_loader
    def load_user(id):
        user = User.query.get(int(id))
        if not user:
            return None
        return user

    # register handler for uncaught errors
    # TODO: maybe move error handler to different module?
    def handle_uncaught_error(error):
        app.logger.error(error)
        return jsonify({'name': 'uncaught error', 'value': 'see flask errors for more info'})

    # TODO: make all views in `views.py` raise `Unauthorized` instead of handling it on their own
    def handle_unauthorized(error):
        return jsonify(SwaggerResponses.AUTHORIZATION_REQUIRED), 401

    app.register_error_handler(Exception, handle_uncaught_error)
    app.register_error_handler(Unauthorized, handle_unauthorized)

    return app


def setup_logger():
    os.makedirs('logs', exist_ok=True)
    date = datetime.now().strftime('%d_%m__%H_%M')
    logging.basicConfig(filename=f'logs/error_{date}.log', level=logging.DEBUG)


if __name__ == '__main__':
    app = create_app('dev')
    setup_logger()
    app.run(host='0.0.0.0')
