from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from instance.config import configs


db = SQLAlchemy()
migrate = Migrate()
ma = Marshmallow()


def create_app(config_name):
    app = Flask(__name__)

    # Take config from `config.py`
    config = configs.get(config_name)
    app.config.from_object(config)
    # Configure database
    app.config['SQLALCHEMY_DATABASE_URI'] = config.DB_URI

    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)

    # Initialize views and db models
    with app.app_context():
        import views
        import model

    return app


if __name__ == '__main__':
    app = create_app('dev')
    app.run()
