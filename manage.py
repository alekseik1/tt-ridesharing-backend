from flask_migrate import MigrateCommand, Manager

from app import create_app

manager = Manager(create_app)
manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()
