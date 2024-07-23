import datetime
import recurring_ical_events

from icalendar import Calendar
from pathlib import Path
from dotenv import dotenv_values

config = dotenv_values(".env")


class YasnoAPI:
    def __init__(self):
        self.ical = None
        peth_to_calendar = Path(__file__).parent.parent / config.get("YASNO_ICAL_PATH")
        with peth_to_calendar.open() as file:
            self.ical = recurring_ical_events.of(Calendar.from_ical(file.read()))

    def get_current_event(self, at: datetime.datetime) -> dict:
        events = self.ical.at(at)
        if events is None:
            return None

        return events[0]


