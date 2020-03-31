import logging
import os
from datetime import datetime

from flask import Flask, request
from flask_cors import CORS
from flask_login import LoginManager
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from elasticsearch import Elasticsearch

from main_app.exceptions import setup_handlers


convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)
db = SQLAlchemy(metadata=metadata)

migrate = Migrate()
ma = Marshmallow()
login = LoginManager()


def create_app():
    # Configure Sentry if possible
    if 'SENTRY_DSN' in os.environ:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        sentry_sdk.init(
            dsn=os.environ['SENTRY_DSN'],
            integrations=[FlaskIntegration(), SqlalchemyIntegration()]
        )
    app = Flask(__name__)

    app.config.from_object('settings.Config')
    app.secret_key = app.config['SECRET_KEY']
    app.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE=None,
    )
    # elasticsearch
    app.elasticsearch = Elasticsearch([app.config['ELASTICSEARCH_URL']]) \
        if app.config['ELASTICSEARCH_URL'] else None

    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)
    # Enable CORS for any ports, any origins
    CORS(app, supports_credentials=True)
    login.init_app(app)
    # register all Blueprints
    from main_app.views import auth, user_and_driver, organization, ride, car, misc     # noqa: F401
    from main_app.views import api
    app.register_blueprint(api)

    from main_app.model import User
    @login.user_loader
    def load_user(id):
        user = User.query.get(int(id))
        if not user:
            return None
        return user

    setup_handlers(app)
    setup_logger(app)
    return app


def setup_logger(app):
    os.makedirs('logs', exist_ok=True)
    date = datetime.now().strftime('%d_%m__%H_%M')
    log_level = logging.ERROR
    if app.debug:
        log_level = logging.DEBUG
    if app.testing:
        log_level = logging.INFO
    logging.basicConfig(filename=f'logs/{app.config.get("LOGGER_NAME", app.name)}_error_{date}.log',
                        level=log_level)

    @app.before_request
    def log_request_info():
        app.logger.debug('Body: %s', request.get_data())


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=app.config['PORT'])
