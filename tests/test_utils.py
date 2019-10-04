from mimesis.providers import Person


def generate_random_person(locale='ru'):
    return Person(locale)
