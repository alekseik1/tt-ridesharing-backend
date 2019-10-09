from flask_testing import TestCase
from app import create_app, db
from flask import url_for
from utils.misc import generate_random_person
from utils.exceptions import ResponseExamples
import unittest


class RegisterUserTests(TestCase):

    def create_app(self):
        return create_app('test')

    def setUp(self) -> None:
        self.app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False
        db.session.close()
        db.drop_all()
        db.create_all()
        from views import register_user
        self.url = url_for('.'+register_user.__name__)

    def test_incorrect_register_status_code(self):
        bad_request_data = [
            {'name': 'aleks'},
            {'surname': 'kozh'},
            {'email': 'a@mail.ru'},
            {'name': 'aleks', 'surname': 'kozh'},
        ]
        for data in bad_request_data:
            result = self.client.post(self.url, data=data)
            self.assertEqual(400, result.status_code)

    def test_incorrect_register_error_details(self):
        # TODO: check for `incorrect_fields` in response
        pass

    def test_register_correct_user(self):
        person = generate_random_person()
        name, surname, email, password = person.name(), person.surname(), person.email(), '1234'
        result = self.client.post(self.url, data={
            'name': name,
            'surname': surname,
            'email': email,
            'password': '12345'
        })
        with self.subTest('Got correct return code'):
            self.assert200(result)
        user = db.session.find_all(email=email).first()
        with self.subTest('User is added to database'):
            self.assertIsNotNone(user)
        with self.subTest('user_id is in response'):
            correct_response = ResponseExamples.USER_ID
            correct_response['user_id'] = user.id
            self.assertEqual(result.get_json(), correct_response)
        with self.subTest("User's password, name and surname are correct"):
            self.assertTrue(user.check_password(password))
            self.assertEqual(name, user.name)
            self.assertEqual(surname, user.surname)

    def test_cannot_register_two_identical_emails(self):
        person = generate_random_person()
        name1, surname1, email, password1 = person.name(), person.surname(), person.email(), '1234'
        name2, surname2, email, password2 = person.name(), person.surname(), email, '2234'
        # Register first user
        self.client.post(self.url, data={
            'name': name1,
            'surname': surname1,
            'email': email,
            'password': '12345'
        })
        # Register second user
        result2 = self.client.post(self.url, data={
            'name': name2,
            'surname': surname2,
            'email': email,
            'password': '12345'
        })
        with self.subTest('status code is 400'):
            self.assert400(result2)
        with self.subTest('correct error'):
            correct_error = ResponseExamples.EMAIL_IS_BUSY
            correct_error['value'] = email
            self.assertEqual(correct_error, result2.get_json())


if __name__ == '__main__':
    unittest.main()
