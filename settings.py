import os


class Config:
    FLASK_ENV = os.environ['FLASK_ENV']
    DEBUG = os.environ['DEBUG']
    TESTING = os.environ['TESTING']
    PRESERVE_CONTEXT_ON_EXCEPTION = os.environ['PRESERVE_CONTEXT_ON_EXCEPTION']
    SQLALCHEMY_TRACK_MODIFICATIONS = os.environ['SQLALCHEMY_TRACK_MODIFICATIONS']
    SQLALCHEMY_DATABASE_URI = os.environ['SQLALCHEMY_DATABASE_URI']
    SECRET_KEY = os.environ['SECRET_KEY']