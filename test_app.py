import unittest
import app as a
from pprint import pprint

class AppTestCase(unittest.TestCase):
    def setUp(self):
        a.app.config['TESTING'] = True
        a.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = a.app.test_client()
        with a.app.app_context():
            a.db.create_all()
            a.init_db()  # Will prepopulate test data since it's empty

    def tearDown(self):
        with a.app.app_context():
            a.db.session.remove()
            a.db.drop_all()

    def test_index_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

    def test_contractors_page(self):
        response = self.app.get('/contractors')
        self.assertEqual(response.status_code, 200)

    def test_products_page(self):
        response = self.app.get('/products')
        self.assertEqual(response.status_code, 200)

    def test_new_invoice_page(self):
        response = self.app.get('/invoice/new')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
