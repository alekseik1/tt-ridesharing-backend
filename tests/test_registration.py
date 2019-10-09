from flask_testing import TestCase
from app import create_app, db
from flask import url_for, jsonify
from utils.misc import generate_random_person
from utils.exceptions import ResponseExamples
from model import User
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
            {'first_name': 'aleks'},
            {'last_name': 'kozh'},
            {'email': 'a@mail.ru'},
            {'first_name': 'aleks', 'last_name': 'kozh'},
        ]
        for data in bad_request_data:
            result = self.client.post(self.url, json=data)
            self.assertEqual(400, result.status_code)

    def test_incorrect_register_error_details(self):
        from itertools import combinations
        correct_data = {
            'first_name': 'Martin',
            'last_name': 'Smith',
            'email': 'm.smith@mail.ru',
            'password': '12345qwerty'
        }

        def _test_routine(params):
            params = list(params)
            tmp = correct_data.copy()
            for p in params:
                tmp.pop(p)
            response = self.client.post(self.url, json=tmp)
            correct_response = ResponseExamples.some_params_are_invalid(params)
            with self.subTest(f'status code: {params}'):
                self.assert400(response)
            with self.subTest(f'correct error raised: {params}'):
                response = response.get_json()
                self.assertEqual(
                    correct_response['name'], response['name'])
                self.assertEqual(
                    sorted(correct_response['value']), sorted(response['value']))

        keys = list(correct_data.keys())
        # Допускаем выкинуть сначала 1, потом 2 и т.д. элементов запроса
        for i in range(1, len(keys) + 1):
            # Состовляем все возможные способы выкинуть i элементов
            for combo in combinations(keys, i):
                # И прогоняем тест
                _test_routine(combo)

    def test_register_correct_user(self):
        person = generate_random_person()
        name, surname, email, password = person.name(), person.surname(), person.email(), '1234'
        result = self.client.post(self.url, json={
            'first_name': name,
            'last_name': surname,
            'email': email,
            'password': password
        })
        with self.subTest('Got correct return code'):
            self.assert200(result)
        user = db.session.query(User).filter_by(email=email).first()
        with self.subTest('User is added to database'):
            self.assertIsNotNone(user)
        with self.subTest('user_id is in response'):
            correct_response = ResponseExamples.USER_ID
            correct_response['user_id'] = user.id
            self.assertEqual(result.get_json(), correct_response)
        with self.subTest("User's password, name and surname are correct"):
            self.assertTrue(user.check_password(password))
            self.assertEqual(name, user.first_name)
            self.assertEqual(surname, user.last_name)

    def test_cannot_register_two_identical_emails(self):
        person = generate_random_person()
        name1, surname1, email, password1 = person.name(), person.surname(), person.email(), '1234'
        name2, surname2, email, password2 = person.name(), person.surname(), email, '2234'
        # Register first user
        self.client.post(self.url, json={
            'first_name': name1,
            'last_name': surname1,
            'email': email,
            'password': password1
        })
        # Register second user
        result2 = self.client.post(self.url, json={
            'first_name': name2,
            'last_name': surname2,
            'email': email,
            'password': password2
        })
        with self.subTest('status code is 400'):
            self.assert400(result2)
        with self.subTest('correct error'):
            correct_error = ResponseExamples.EMAIL_IS_BUSY
            correct_error['value'] = email
            self.assertEqual(correct_error, result2.get_json())


if __name__ == '__main__':
    unittest.main()
