from datetime import datetime

from unittest.mock import patch, MagicMock
from main import app, db
import unittest
import json
from pathlib import Path

from models.signal import Signal


class TestApi(unittest.TestCase):
    __current_mocked_datetime = datetime(2024, 7, 29, 3, 0, 0)
    __last_signal_time = datetime(2024, 7, 29, 2, 0, 0)

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
        signal = Signal(timestamp=cls.__last_signal_time)
        db.session.add(signal)
        db.session.commit()

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.drop_all()

    @patch('yasno.api.requests')
    @patch('main.datetime')
    @patch('yasno.power_state.datetime')
    @patch('yasno.api.datetime')
    def test_status_endpoint(self, yasno_api_mock_datetime, yasno_power_mock_datetime, main_mock_datetime, mocked_request):
        # when
        with open(Path(__file__).parent / "__mocks__/http_calendar.json") as f:
            mocked_data = json.load(f)

        # when
        main_mock_datetime.now.return_value = self.__current_mocked_datetime
        yasno_power_mock_datetime.now.return_value = self.__current_mocked_datetime
        yasno_api_mock_datetime.now.return_value = self.__current_mocked_datetime

        # when
        mocked_request.get.return_value.status_code = 200
        mocked_request.get.return_value.json.return_value = mocked_data
        response = self.client.get('/status')

        # then
        self.assertEqual(response.status_code, 200)
        self.assertIn("has_electricity", response.json)
        self.assertEqual({
            "has_electricity": False,
            "message": "Світло може повернутись в 05:00 якщо не буде застосовано світло-сірі зони"
        } ,response.json)

if __name__ == '__main__':
    unittest.main()
