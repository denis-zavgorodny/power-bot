from datetime import datetime
from typing import Dict

from yasno.api import YasnoAPI

START = "DTSTART"
END = "DTEND"
KIND = "SUMMARY"
GREY = "maybe"
DARK = "off"


class Power:
    def __init__(self, calendar: YasnoAPI):
        self.calendar = calendar

    class Prediction(Dict):
        has_electricity: bool
        message: str

    def predict(self, has_electricity: bool) -> Prediction:
        message = self.__get_message(has_electricity)

        return self.Prediction(has_electricity=has_electricity, message=message)

    def __get_message(self, has_electricity: bool) -> str:
        currentState = self.calendar.get_current_event(at=datetime.now())
        if has_electricity is True and currentState is None:
            nextState = self.calendar.next_off()
            next_date = nextState.decoded(START).strftime("%Y-%m-%d %H:%M")
            message = f"Наступне відключення: {next_date}"
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

    def __is_dark_zone(self, state: Dict) -> bool:
        return state.get(KIND) == DARK

    def __is_grey_zone(self, state: Dict) -> bool:
        return state.get(KIND) == GREY
