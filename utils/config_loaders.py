from os import environ
from instance.config import configs


def load_config():
    return configs[environ['FLASK_CONFIG_TYPE']]
