from flask_testing import TestCase
from app import create_app, db
from fill_db import fill_database


class TestWithDatabase(TestCase):

    def create_app(self):
        return create_app()

    def setUp(self) -> None:
        db.drop_all()
        db.create_all()
        fill_database(app=self.app)
