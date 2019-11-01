from flask import url_for
from flask_testing import TestCase
from main_app.model import User
from utils.misc import generate_random_person
from app import db, create_app
from utils.exceptions import ResponseExamples


class LoginTests(TestCase):

    def create_app(self):
        return create_app('test')

    def _add_user_with_password(self, password):
        person = generate_random_person()
        first_name, last_name, email = person.name(), person.surname(), person.email()
        user = User(first_name=first_name, last_name=last_name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return email, password

    def setUp(self) -> None:
        self.app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False
        db.session.close()
        db.drop_all()
        db.create_all()
        from main_app.views import login
        self.url = url_for('.'+login.__name__)
        self.email, self.password = self._add_user_with_password('1234')

    def test_incorrect_login(self):
        login_result = self.client.post(self.url, json={
            'login': self.email,
            # Here we add extra char
            'password': self.password + '1'
        })
        correct_answer = ResponseExamples.INCORRECT_LOGIN
        self.assert400(login_result)
        self.assertEqual(login_result.get_json(), correct_answer)

    def test_user_gets_cookies_after_login(self):
        result = self.client.post(self.url, json={
            'login': self.email,
            'password': self.password
        })
        cookies = result.headers['Set-Cookie']
        self.assertTrue(len(cookies) > 0, "Didn't receive any cookies")

    def test_correct_login(self):
        login_result = self.client.post(self.url, json={
            'login': self.email,
            'password': self.password
        })
        with self.subTest('correct status code'):
            self.assert200(login_result)
        with self.subTest('response is {user_id: ##}'):
            # True user ID
            user_id = db.session.query(User).filter(User.email == self.email).first().id
            # Form expected result
            correct_answer = ResponseExamples.USER_ID
            correct_answer['user_id'] = user_id
            self.assertEqual(login_result.get_json(), correct_answer)

    def test_return_error_when_already_logged_in(self):
        login_result = self.client.post(self.url, json={
            'login': self.email,
            'password': self.password
        })
        second_request = self.client.post(self.url, json={
            'login': self.email,
            'password': self.password
        })
        with self.subTest('correct status code'):
            self.assert400(second_request)
        with self.subTest('correct error'):
            self.assertEqual(ResponseExamples.ALREADY_LOGGED_IN, second_request.get_json())
