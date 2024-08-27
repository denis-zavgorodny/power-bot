from datetime import datetime, timedelta
from typing import Dict
from timezone import timezone

import pytz

from logger import get_logger
from yasno.api import YasnoAPI

START = "DTSTART"
END = "DTEND"
KIND = "SUMMARY"
GREY = "maybe"
DARK = "off"


class Power:
    def __init__(self, calendar: YasnoAPI):
        self.calendar = calendar
        self.logger = get_logger()

    class Prediction(Dict):
        has_electricity: bool
        message: str

    def predict(self, has_electricity: bool) -> Prediction:
        try:
            message = self.__get_message(has_electricity)
            return self.Prediction(has_electricity=has_electricity, message=message)
        except Exception as e:
            self.logger.error(f"Prediction error: {e}")
            return self.Prediction(has_electricity=has_electricity)

    def __get_message(self, has_electricity: bool) -> str:
        currentState = self.calendar.get_current_event(at=datetime.now(tz=timezone))
        if has_electricity is True and currentState is None:
            nextState = self.calendar.next_off()
            next_date = nextState.decoded(START).strftime("%Y-%m-%d %H:%M")
            next_time = nextState.decoded(START).strftime("%H:%M")
            w = self.__is_today(nextState.decoded(START))
            text_day = ""
            if self.__is_today(nextState.decoded(START)):
                text_day = f"сьогодні о {next_time}"
            elif self.__is_tomorrow(nextState.decoded(END)):
                text_day = f"завтра о {next_time}"
            else:
                text_day = next_date

            message = f"Наступне відключення {text_day}"
        elif has_electricity is True and currentState is not None:
            next_date = currentState.decoded(END).strftime("%H:%M")
            message = f"Світло все ще можуть вимкнути до {next_date}"
        elif has_electricity is False and currentState is None:
            message = "Планового відключення не мало б бути"
        else:
            if self.__is_dark_zone(currentState):
                next_date = currentState.decoded(END).strftime("%H:%M")
                message = f"Світло може повернутись в {next_date} якщо не буде застосовано світло-сірі зони"
            else:
                next_date = currentState.decoded(END).strftime("%H:%M")
                message = f"Світло має повернутись до {next_date}. Зараз діє світло-сіра зона, світло можуть ввімкнути в будь-який момент"

        return message

    def __is_today(self, date: datetime) -> bool:
        start = datetime.now(tz=timezone).replace(hour=0, minute=0, second=0, microsecond=0)
        end = datetime.now(tz=timezone).replace(hour=23, minute=59, second=59, microsecond=999999)

        try:
            return end >= date >= start
        except Exception as e:
            self.logger.error(f"Day detection error: {e}")
            return False


    def __is_tomorrow(self, date: datetime) -> bool:
        start = datetime.now(tz=timezone).replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        end = datetime.now(tz=timezone).replace(hour=23, minute=59, second=59, microsecond=0) + timedelta(days=1)

        try:
            return end >= date >= start
        except Exception as e:
            self.logger.error(f"Day detection error: {e}")
            return False


    def __is_dark_zone(self, state: Dict) -> bool:
        return state.get(KIND) == DARK

    def __is_grey_zone(self, state: Dict) -> bool:
        return state.get(KIND) == GREY
