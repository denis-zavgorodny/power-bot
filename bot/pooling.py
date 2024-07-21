import time

import requests

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from logger import get_logger

logger = get_logger()


def pooling_status(endpoint, callback, interval=3):
    isElectricityAvailable = None

    while True:
        try:
            session = requests_session_with_retries(retries=3, backoff_factor=0.5)
            response = session.get(endpoint)
            response.raise_for_status()
            res = response.json()

            if res["hasElectricity"] is True:
                if isElectricityAvailable is False:
                    callback(True)

                isElectricityAvailable = True

            else:
                if isElectricityAvailable is True:
                    callback(False)

                isElectricityAvailable = False

        except requests.exceptions.RequestException as e:
            logger.error(f"Pooling status request failed: {e}")

        time.sleep(interval)


def requests_session_with_retries(retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 504)):
    session = requests.Session()

    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )

    adapter = HTTPAdapter(max_retries=retry)

    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session
