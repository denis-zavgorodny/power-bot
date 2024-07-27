from datetime import datetime

from main import app, db
import unittest

from models.signal import Signal


class TestApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.testing = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        cls.client = app.test_client()
        with app.app_context():
            db.create_all()
            cls.setup_mock_data()

    @classmethod
    def setup_mock_data(cls):

        signal = Signal(timestamp=datetime.now())
        db.session.add(signal)
        db.session.commit()

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.drop_all()

    def test_get_endpoint(self):
        response = self.client.get('/status')
        self.assertEqual(response.status_code, 200)
        self.assertIn("has_electricity", response.json)
        self.assertIn("message", response.json)

if __name__ == '__main__':
    unittest.main()
