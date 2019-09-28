from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from instance.config import development_config as config
from .hacks import init_mysql_driver

app = Flask(__name__)

# Take config from `config.py`
app.config.from_object(config)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = config.DB_URI
db = SQLAlchemy(app)
# We import db from 'model.py' and thus force model instantiation (required for proper migration)
from .model import db

# Set up command manager
manager = Manager(app)

# Add db migration commands via command manager
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)

init_mysql_driver()

# Export ready application
ready_app = manager
