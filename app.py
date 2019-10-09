from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from flask_login import LoginManager
from instance.config import configs
from utils.exceptions import InvalidData


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
    login.init_app(app)
    # register all Blueprints
    from views import api
    app.register_blueprint(api)

    # register handler for uncaught errors
    # TODO: maybe move error handler to different module?
    def handle_uncaught_error(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response, error.status_code

    app.register_error_handler(Exception, handle_uncaught_error)

    return app


if __name__ == '__main__':
    app = create_app('dev')
    app.run()
