import datetime
import os

import pytest

from rpi.subservices.aemet import WeatherRecordsManager


def test_weather_records_manager():
    wrm = WeatherRecordsManager.valladolid()
    today = datetime.datetime.today().date()

    assert wrm.mm(today) >= 0
    assert wrm.mean_probability_percentage(today) >= 0


if __name__ == '__main__':
    pytest.main([os.path.basename(__file__), '-v'])
