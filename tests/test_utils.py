import sqlalchemy
from instance.config import test_config as config
from hacks import init_mysql_driver


def create_test_db():
    init_mysql_driver()
    engine = sqlalchemy.create_engine(config.DB_URI_NODB)
    conn = engine.connect()
    conn.execute('commit')
    conn.execute('CREATE DATABASE IF NOT EXISTS {};'.format(config.DB_NAME))
    conn.close()


def drop_test_db():
    init_mysql_driver()
    engine = sqlalchemy.create_engine(config.DB_URI_NODB)
    conn = engine.connect()
    conn.execute('commit')
    conn.execute('DROP DATABASE IF EXISTS {};'.format(config.DB_NAME))
    conn.close()
