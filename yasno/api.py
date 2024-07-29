from datetime import datetime, timedelta
import recurring_ical_events
import requests
import requests_cache

from icalendar import Calendar, Event
from pathlib import Path
from dotenv import dotenv_values
from dateutil.rrule import WEEKLY, rrule

from logger import get_logger

config = dotenv_values(".env")

MAYBE = "maybe"
OFF = "off"

START_OF_DAY = 0
END_OF_DAY = 24

START = "DTSTART"
END = "DTEND"
KIND = "SUMMARY"

requests_cache.install_cache('calendar_cache', expire_after=3600)

#
# The implementation has been copied from HA integration:
# https://github.com/denysdovhan/ha-yasno-outages/blob/main/custom_components/yasno_outages/api.py
# Kudos to @denysdovhan
class YasnoAPI:
    __city = "kiev"
    __group = "group_2"

    def __init__(self, autoload: bool = True):
        self.logger = get_logger()
        self.ical = None
        self.schedule = None
        self.autoload = autoload

        if self.autoload is True:
            self.schedule = self.__load_calendar()
        else:
            peth_to_calendar = Path(__file__).parent.parent / config.get("YASNO_ICAL_PATH")
            with peth_to_calendar.open() as file:
                self.ical = recurring_ical_events.of(Calendar.from_ical(file.read()))


    def get_current_event(self, at: datetime) -> dict | None:
        if self.autoload is True:
            raw = self.__get_current_event(at=datetime.now() + timedelta(hours=0))
            if raw is None:
                return None

            event = Event()
            event.add(KIND, self.__convert_kind_to_ical(raw.get("summary")))
            event.add(START, raw.get("start"))
            event.add(END, raw.get("end"))

            return event

        elif self.ical is not None:
            events = self.ical.at(at)

            if events is None:
                return None
            elif len(events) == 0:
                return None
            return events[0]
        else:
            return None

    def next_off(self):
        if self.autoload is True:
            raw = self.__get_next_off()

            event = Event()
            event.add(KIND, self.__convert_kind_to_ical(raw.get("type")))
            event.add(START, raw.get("start"))
            event.add(END, raw.get("end"))

            return event

        else:
            events = self.ical.between(start=datetime.now(), stop=datetime.now() + timedelta(days=1))

            if events is None:
                return None
            elif len(events) == 0:
                return None

            filtered = list(filter(lambda x: x.get("SUMMARY") == "off", events))
            return filtered[0]

    def __convert_kind_to_ical(self, kind: str) -> str | None:
        if kind == "POSSIBLE_OUTAGE":
            return MAYBE
        elif kind == "DEFINITE_OUTAGE":
            return OFF
        else:
            return None

    def __load_calendar(self):
        try:
            response = requests.get(config.get("YASNO_API_URL"), timeout=60)
            response.raise_for_status()
            res =response.json()

            component = next(
                (
                    item
                    for item in res["components"]
                    if item["template_name"] == "electricity-outages-schedule"
                ),
                None,
            )

            if component:
                return component["schedule"]

            self.logger.log("Could not extract schedule from API")

            return None
        except Exception as e:
            self.logger.error("Fetching schedule from API error: {e}")
            return None

    def __get_current_event(self, at: datetime) -> dict | None:
        """Get the current event."""
        for event in self.__get_events(at, at + timedelta(days=1)):
            if event["start"] <= at < event["end"]:
                return event
        return None
    def __get_next_off(self):
        for event in self.__get_events(datetime.now(), datetime.now() + timedelta(days=1)):
            if event["summary"] == "DEFINITE_OUTAGE":
                return event
        return None

    def __get_city_groups(self, city: str) -> dict[str, list]:
        """Get all schedules for all of available groups for a city."""
        if self.schedule is None:
            raise Exception("Schedule is not ready")
        return self.schedule.get(city, {}) if self.schedule else {}

    def __get_group_schedule(self, city: str, group: str) -> list:
        """Get the schedule for a specific group."""
        city_groups = self.__get_city_groups(city)
        return city_groups.get(self.__group, [])

    def __build_event_hour(
            self,
            date: datetime,
            start_hour: int,
    ) -> datetime:
        return date.replace(hour=start_hour, minute=0, second=0, microsecond=0)

    def __get_events(
            self,
            start_date: datetime,
            end_date: datetime,
    ) -> list[dict]:
        """Get all events."""
        if not self.__city or not self.__group:
            return []
        group_schedule = self.__get_group_schedule(self.__city, self.__group)
        events = []



        # For each day of the week in the schedule
        for dow, day_events in enumerate(group_schedule):
            # Build a recurrence rule the events between start and end dates
            recurrance_rule = rrule(
                WEEKLY,
                dtstart=start_date,
                until=end_date,
                byweekday=dow,
            )

            # For each event in the day
            for event in day_events:
                event_start_hour = event["start"]
                event_end_hour = event["end"]

                if event_end_hour == END_OF_DAY:
                    event_end_hour = START_OF_DAY

                # For each date in the recurrence rule
                for dt in recurrance_rule:
                    event_start = self.__build_event_hour(dt, event_start_hour)
                    event_end = self.__build_event_hour(dt, event_end_hour)
                    if event_end_hour == START_OF_DAY:
                        event_end += timedelta(days=1)
                    if (
                            start_date <= event_start <= end_date
                            or start_date <= event_end <= end_date
                            # Include events that intersect beyond the timeframe
                            # See: https://github.com/denysdovhan/ha-yasno-outages/issues/14
                            or event_start <= start_date <= event_end
                            or event_start <= end_date <= event_end
                    ):
                        events.append(
                            {
                                "summary": event["type"],
                                "start": event_start,
                                "end": event_end,
                            },
                        )

        # Sort events by start time to ensure correct order
        return sorted(events, key=lambda event: event["start"])


