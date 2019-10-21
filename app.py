from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from flask_login import LoginManager
from instance.config import configs
from utils.exceptions import ResponseExamples
from werkzeug.exceptions import Unauthorized
from utils.exceptions import InvalidData
from flask_cors import CORS


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
    from views import api
    app.register_blueprint(api)

    from model import User
    @login.user_loader
    def load_user(id):
        user = User.query.get(int(id))
        if not user:
            return None
        return user

    # register handler for uncaught errors
    # TODO: maybe move error handler to different module?
    def handle_uncaught_error(error):
        return error

    # TODO: make all views in `views.py` raise `Unauthorized` instead of handling it on their own
    def handle_unauthorized(error):
        return ResponseExamples.AUTHORIZATION_REQUIRED, 401

    app.register_error_handler(Exception, handle_uncaught_error)
    app.register_error_handler(Unauthorized, handle_unauthorized)

    return app


if __name__ == '__main__':
    app = create_app('dev')
    app.run()
