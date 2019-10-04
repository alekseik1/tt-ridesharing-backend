from flask import url_for
from flask_testing import TestCase
from app import db, create_app


class APITest(TestCase):

    def create_app(self):
        return create_app('test')

    def setUp(self) -> None:
        self.client = self.app.test_client()
        db.session.close()
        db.drop_all()
        db.create_all()

    def test_register_incorrect_user(self):
        from views import register_user
        url = url_for(register_user.__name__)
        bad_request_data = [
            {'name': 'aleks'},
            {'surname': 'kozh'},
            {'email': 'a@mail.ru'},
            {'name': 'aleks', 'surname': 'kozh'},
        ]
        for data in bad_request_data:
            result = self.client.post(url, data=data)
            self.assertEqual(400, result.status_code)
