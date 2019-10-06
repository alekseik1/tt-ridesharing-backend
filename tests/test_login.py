from flask import url_for
from flask_testing import TestCase
from model import User
from utils.misc import generate_random_person
from app import db, create_app


class APITest(TestCase):

    def create_app(self):
        return create_app('test')

    def _add_user_with_password(self, password):
        person = generate_random_person()
        name, surname, email = person.name(), person.surname(), person.email()
        user = User(name=name, surname=surname, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return email, password

    def setUp(self) -> None:
        self.app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False
        db.session.close()
        db.drop_all()
        db.create_all()

    def test_incorrect_login(self):
        from views import login
        url = url_for('.'+login.__name__)
        email, password = self._add_user_with_password('1234')
        login_result = self.client.post(url,
                                        data={'email': email,
                                              # Here we add extra char
                                              'password': password + '1'}
                                        )
        # Check if we're redirected to login page
        self.assertTrue(login_result.headers.get('Location')
                        .endswith(url_for('.'+login.__name__)))

    def test_user_gets_cookies_after_login(self):
        from views import login
        # Create user
        email, password = self._add_user_with_password('1234')
        url = url_for('.'+login.__name__)
        result = self.client.post(url, data={'email': email, 'password': password})
        cookies = result.headers['Set-Cookie']
        self.assertTrue(len(cookies) > 0, "Didn't receive any cookies")

    def test_user_is_redirected_to_index_page_after_login(self):
        from views import login, index
        # Create user
        email, password = self._add_user_with_password('1234')
        url = url_for('.'+login.__name__)
        result = self.client.post(url, data={'email': email, 'password': password})
        self.assertEqual(302, result.status_code, "status code didn't match")
        self.assertTrue(result.headers.get('Location')
                        .endswith(url_for('.'+index.__name__)), "No redirect to index page")

    def test_authenticated_user_is_redirected_to_index_page_after_accessing_login_page(self):
        from views import login, index
        # Create user
        email, password = self._add_user_with_password('1234')
        url = url_for('.'+login.__name__)
        result = self.client.post(url, data={'email': email, 'password': password})
        cookies = result.headers['Set-Cookie']
        login_result = self.client.post(url_for('.'+login.__name__))
        # Check the status code
        self.assertEqual(302, login_result.status_code, "status code didn't match")
        # Check if we're redirected to index page
        self.assertTrue(login_result.headers.get('Location').endswith(index.__name__), "No redirect to index page")
