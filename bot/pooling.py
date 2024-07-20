import time

import requests


def poolingStatus(endpoint, callback, interval=60):
    isElectricityAvailable = None

    while True:
        try:
            response = requests.get(endpoint)

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
