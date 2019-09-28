import unittest
from tests.test_utils import create_test_db, drop_test_db


class ModelTest(unittest.TestCase):

    def setUp(self):
        drop_test_db()
        create_test_db()

    def tearDown(self):
        drop_test_db()

    def test_add_user(self):
        pass

    def test_add_driver(self):
        pass