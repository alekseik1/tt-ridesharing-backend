from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from flask_marshmallow import Marshmallow
from utils.misc import load_config

config = load_config()

app = Flask(__name__)
ma = Marshmallow(app)

# Take config from `config.py`
app.config.from_object(config)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = config.DB_URI
db = SQLAlchemy(app)
# We import db from 'model.py' and thus force model instantiation (required for proper migration)
from .model import db
# We import everything from `views.py` and thus create all app routes
from views import *

# Set up command manager
manager = Manager(app)

# Add db migration commands via command manager
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)

# Export ready application
ready_app = manager
