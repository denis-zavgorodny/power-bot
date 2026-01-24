import time
import json
import os

import requests

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from logger import get_logger

logger = get_logger()

STATE_FILE = os.path.join(os.path.dirname(__file__), "..", "electricity_state.json")


def load_electricity_state():
    """Load the electricity state from the persistent file."""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                data = json.load(f)
                state = data.get("isElectricityAvailable")
                logger.info(f"Loaded electricity state from file: {state}")
                return state
    except Exception as e:
        logger.error(f"Failed to load electricity state from file: {e}")
    return None


def save_electricity_state(isElectricityAvailable):
    """Save the electricity state to the persistent file."""
    try:
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        with open(STATE_FILE, 'w') as f:
            json.dump({"isElectricityAvailable": isElectricityAvailable}, f)
        logger.debug(f"Saved electricity state to file: {isElectricityAvailable}")
    except Exception as e:
        logger.error(f"Failed to save electricity state to file: {e}")


def pooling_status(endpoint, callback, interval=30):
    isElectricityAvailable = load_electricity_state()

    while True:
        try:
            session = requests_session_with_retries(retries=3, backoff_factor=0.5)
            response = session.get(endpoint)
            response.raise_for_status()
            res = response.json()

            if res["has_electricity"] is True:
                if isElectricityAvailable is False:
                    callback(True)

                isElectricityAvailable = True
                save_electricity_state(isElectricityAvailable)

            else:
                if isElectricityAvailable is True:
                    callback(False)

                isElectricityAvailable = False
                save_electricity_state(isElectricityAvailable)

            logger.info(f"Pooling status: {isElectricityAvailable}")

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
