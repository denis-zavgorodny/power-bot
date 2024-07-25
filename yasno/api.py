import datetime
import recurring_ical_events

from icalendar import Calendar
from pathlib import Path
from dotenv import dotenv_values

config = dotenv_values(".env")

MAYBE = "maybe"
OFF = "off"

class YasnoAPI:
    def __init__(self):
        self.ical = None
        peth_to_calendar = Path(__file__).parent.parent / config.get("YASNO_ICAL_PATH")
        with peth_to_calendar.open() as file:
            self.ical = recurring_ical_events.of(Calendar.from_ical(file.read()))

    def get_current_event(self, at: datetime.datetime) -> dict | None:
        events = self.ical.at(at)
        if events is None:
            return None
        return events[0]

    def next_off(self):
        events = self.ical.between(start=datetime.datetime.now(), stop=datetime.datetime.now() + datetime.timedelta(days=1))
        if events is None:
            return None

        filtered = list(filter(lambda x: x.get("SUMMARY") == "off", events))
        return filtered[0]


