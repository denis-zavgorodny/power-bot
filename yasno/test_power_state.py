import unittest
from datetime import datetime
from unittest.mock import patch
from yasno.api import YasnoAPI
from yasno.power_state import Power

power = Power(calendar=YasnoAPI())


class Test(unittest.TestCase):
    @patch('yasno.power_state.datetime')
    def test_power_state_when_no_power_and_it_is_expected(self, mock_datetime):
        mock_datetime.now.return_value = datetime(2024, 7, 22, 19, 0, 0)
        self.assertEqual(
            power.predict(has_electricity=False),
            {'has_electricity': False, 'message': 'Світло має повернутись в 22:00'}
        )

    @patch('yasno.power_state.datetime')
    def test_power_state_when_no_power_and_it_is_not_expected(self, mock_datetime):
        mock_datetime.now.return_value = datetime(2024, 7, 22, 17, 0, 0)
        self.assertEqual(
            power.predict(has_electricity=False),
            {'has_electricity': False, 'message': 'Планового відключення не мало б бути'}
        )


if __name__ == '__main__':
    unittest.main()
