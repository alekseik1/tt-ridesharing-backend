from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from instance.config import DevelopmentConfig as config

app = Flask(__name__)

# Take config from `config.py`
app.config.from_object(config)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = config.DATABASE_URI
db = SQLAlchemy(app)

# Set up command manager
manager = Manager(app)

# Add db migration commands via command manager
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)

# Export ready application
ready_app = manager
