import os
from dotenv import load_dotenv
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

MAX_EMAIL_LENGTH = 256
MAX_NAME_LENGTH = 40
MAX_SURNAME_LENGTH = 40
MAX_URL_LENGTH = 2000
BLUEPRINT_API_NAME = 'api'


class Config:
    """
    All variables are for production by default
    """
    SECRET_KEY = os.environ['SECRET_KEY']
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
    PORT = os.environ.get('PORT', 5000)

    PRESERVE_CONTEXT_ON_EXCEPTION = os.environ.get('PRESERVE_CONTEXT_ON_EXCEPTION', False)
    SQLALCHEMY_TRACK_MODIFICATIONS = os.environ.get('SQLALCHEMY_TRACK_MODIFICATIONS', False)
    FLASK_ENV = os.environ.get('FLASK_ENV', 'production')
    DEBUG = os.environ.get('DEBUG', False)
    TESTING = os.environ.get('TESTING', False)
    FCM_BACKEND_URL = os.environ.get('FCM_BACKEND_URL')

    S3_BUCKET = os.environ.get('S3_BUCKET')
    S3_URL = os.environ.get('S3_URL')
