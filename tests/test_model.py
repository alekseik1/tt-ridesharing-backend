from utils.misc import generate_random_person
from app import db, create_app
from model import User, Driver
from flask_testing import TestCase


class ModelTest(TestCase):

    def create_app(self):
        return create_app('test')

    def setUp(self):
        db.session.close()
        db.drop_all()
        db.create_all()

    def tearDown(self):
        db.session.close()
        db.drop_all()

    def test_simply_add_user(self):
        for i in range(10):
            person = generate_random_person()
            db.session.add(User(
                name=person.name(),
                surname=person.surname(),
                email=person.email(),
                is_trusful=(True if i % 2 == 0 else False)
            ))
        db.session.commit()
        all_added = db.session.query(User)
        # Check if users were added
        self.assertNotEqual(len(list(all_added)), 0)

    def test_add_driver(self):
        for i in range(10):
            person = generate_random_person()
            db.session.add(Driver(
                name=person.name(),
                surname=person.surname(),
                email=person.email(),
                is_trusful=True,
                driver_license_1='https://our.storage.com/your_lisence_1.png',
                driver_license_2='https://our.storage.com/your_lisence_2.png',
                passport_1='https://our.storage.com/your_passport_1.png',
                passport_2='https://our.storage.com/your_passport_2.png',
                passport_selfie='https://our.storage.com/your_passport_selfie.png',
            ))
        db.session.commit()
        all_added = db.session.query(Driver)
        self.assertNotEqual(len(list(all_added)), 0)
