from flask_testing import TestCase
from app import create_app, db
from flask import url_for


class RegistrationTest(TestCase):

    def create_app(self):
        return create_app('test')

    def setUp(self) -> None:
        self.app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False
        db.session.close()
        db.drop_all()
        db.create_all()

    def test_register_incorrect_user(self):
        from views import register_user
        url = url_for('.'+register_user.__name__)
        bad_request_data = [
            {'name': 'aleks'},
            {'surname': 'kozh'},
            {'email': 'a@mail.ru'},
            {'name': 'aleks', 'surname': 'kozh'},
        ]
        for data in bad_request_data:
            result = self.client.post(url, data=data)
            self.assertEqual(400, result.status_code)
