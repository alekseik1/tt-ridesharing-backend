from os import environ

from mimesis import Person

from instance.config import configs


def load_config():
    return configs[environ['FLASK_CONFIG_TYPE']]


def generate_random_person(locale='ru'):
    return Person(locale)