import time

import requests

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def poolingStatus(endpoint, callback, interval=60):
    session = requests_session_with_retries(retries=3, backoff_factor=1)
    isElectricityAvailable = None

    while True:
        try:
            response = session.get(endpoint)
            response.raise_for_status()


            if response.status_code == 200:
                if isElectricityAvailable is False:
                    callback(True)

                isElectricityAvailable = True

            else:
                if isElectricityAvailable is True:
                    callback(False)

                isElectricityAvailable = False

        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")

        time.sleep(interval)


def requests_session_with_retries(retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 504, 404)):
    session = requests.Session()

    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        backoff_max=10
    )

    adapter = HTTPAdapter(max_retries=retry)

    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session
