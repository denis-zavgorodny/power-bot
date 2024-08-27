import unittest
from datetime import datetime
from unittest.mock import patch
from yasno.api import YasnoAPI
from yasno.power_state import Power

class Test(unittest.TestCase):
    @patch('yasno.power_state.datetime')
    def test_power_state_when_no_power_in_dark_zone_and_it_is_expected(self, mock_datetime):
        # when
        power = Power(calendar=YasnoAPI(autoload=False))
        mock_datetime.now.return_value = datetime(2024, 7, 22, 19, 0, 0)

        # then
        self.assertEqual(
            power.predict(has_electricity=False),
            {'has_electricity': False, 'message': 'Світло може повернутись в 22:00 якщо не буде застосовано світло-сірі зони'}
        )

    @patch('yasno.power_state.datetime')
    def test_power_state_when_no_power_in_grey_zone_and_it_is_expected(self, mock_datetime):
        # when
        power = Power(calendar=YasnoAPI(autoload=False))
        mock_datetime.now.return_value = datetime(2024, 7, 22, 23, 0, 0)

        # then
        self.assertEqual(
            power.predict(has_electricity=False),
            {'has_electricity': False, 'message': 'Світло має повернутись до 01:00. Зараз діє світло-сіра зона, світло можуть ввімкнути в будь-який момент'}
        )

    @patch('yasno.power_state.datetime')
    def test_power_state_when_no_power_and_it_is_not_expected(self, mock_datetime):
        # when
        power = Power(calendar=YasnoAPI(autoload=False))
        mock_datetime.now.return_value = datetime(2024, 7, 22, 17, 0, 0)

        # then
        self.assertEqual(
            power.predict(has_electricity=False),
            {'has_electricity': False, 'message': 'Планового відключення не мало б бути'}
        )

    @patch('yasno.api.datetime')
    @patch('yasno.power_state.datetime')
    def test_power_state_when_power_and_it_is_expected(self, mock_datetime, mock_api_datetime):
        # when
        power = Power(calendar=YasnoAPI(autoload=False))
        mock_datetime.now.return_value = datetime(2024, 7, 22, 16, 0, 0)
        mock_api_datetime.now.return_value = datetime(2024, 7, 22, 16, 0, 0)

        # then
        self.assertEqual(
            {'has_electricity': True, 'message': 'Наступне відключення 2024-07-22 18:00'},
            power.predict(has_electricity=True)
        )

    @patch('yasno.api.datetime')
    @patch('yasno.power_state.datetime')
    def test_power_state_when_power_and_it_is_not_expected(self, mock_datetime, mock_api_datetime):
        # when
        power = Power(calendar=YasnoAPI(autoload=False))
        mock_datetime.now.return_value = datetime(2024, 7, 22, 19, 0, 0)
        mock_api_datetime.now.return_value = datetime(2024, 7, 22, 19, 0, 0)

        # then
        self.assertEqual(
            power.predict(has_electricity=True),
            {'has_electricity': True, 'message': 'Світло все ще можуть вимкнути до 22:00'}
        )


if __name__ == '__main__':
    unittest.main()
