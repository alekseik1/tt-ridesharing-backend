import logging
import os
import sys
from dotenv import load_dotenv
from datetime import datetime
import boto3
from botocore.client import Config

from flask import Flask, request
from flask_cors import CORS
from flask_login import LoginManager
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from elasticsearch import Elasticsearch

from main_app.exceptions import setup_handlers


dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)


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


def init_elastic(app: Flask):
    from main_app.model import Organization
    searchable = (Organization, )
    app.elasticsearch = Elasticsearch([app.config['ELASTICSEARCH_URL']]) \
        if app.config['ELASTICSEARCH_URL'] else None
    if app.elasticsearch:
        for model in searchable:
            if not app.elasticsearch.indices.exists(index=model.__tablename__):
                app.elasticsearch.indices.create(index=model.__tablename__)


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

    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)
    # Enable CORS for any ports, any origins
    CORS(app, supports_credentials=True)
    login.init_app(app)
    # register all Blueprints
    from main_app.views import auth, user_and_driver, organization, ride, car, misc, dev_utils     # noqa
    from main_app.views import api
    init_elastic(app)
    app.register_blueprint(api)

    from main_app.model import User
    @login.user_loader
    def load_user(id):
        user = User.query.get(int(id))
        if not user:
            return None
        return user

    # S3 storage
    #app.s3_client = boto3.client('s3', endpoint_url=app.config['S3_URL']) \
    #    if app.config.get('S3_URL') else None
    app.s3_client = boto3.client(
        's3',
        config=Config(signature_version='s3v4', region_name='eu-north-1',),
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
    )

    setup_handlers(app)
    setup_logger(app)
    return app


def setup_logger(app):
    log_level = logging.ERROR
    if app.debug:
        log_level = logging.DEBUG
    if app.testing:
        log_level = logging.INFO
    logging.basicConfig(stream=sys.stdout, level=log_level)

    @app.before_request
    def log_request_info():
        app.logger.debug('Body: %s', request.get_data())


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=app.config['PORT'])
