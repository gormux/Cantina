"""
Calendar generation
"""
from workalendar.europe import France
from ics import Calendar as icsCalendar, Event
from requests import Session
import arrow
from pprint import pprint as pp  # noqa

# from app import db

import locale

locale.setlocale(locale.LC_ALL, "fr_FR.UTF-8")

NON_WORKING_DAYS = [3]


def getBookedData(booking_type, username=None):
    booking_data = booking_type.query.filter(booking_type.username == username).scalar()
    if booking_data:
        return booking_data.booked.split()
    else:
        return []


class Calendar:
    """Calendar Object
    """

    def __init__(self, school_year):
        """Creates the class

        :param school_year: Starting year for the school year
        :type school_year: int
        """

        # Initialize school calendar
        school_calendar = {}

        # Get holidays from National Education Ministry
        with open("Calendrier_Scolaire_Zone_B.ics", "r") as cal:
            edu_calendar = icsCalendar(cal.read())

        # Initialize days off ICS calendar
        days_off_school = icsCalendar()

        # Define begin/end of the school year we are in
        for event in edu_calendar.events:
            if (
                "Rentrée scolaire des élèves" in event.name
                and event.begin.year == school_year
            ):
                school_begin = event.begin
                continue
            if "Vacances d'été" in event.name and event.begin.year == school_year + 1:
                school_end = event.begin
                days_off_school.events.add(event)
                continue

        # Add events between begin and end of school year
        # First add school holidays, starting the day after the beginning
        for event in edu_calendar.events:
            if event.begin > school_begin and event.begin < school_end:
                # Remove 1s to end so that it does not overrides next day
                event._end_time = event._end_time.shift(seconds=-1)
                days_off_school.events.add(event)

        # Then take holidays from workalendar
        calendar = France()
        for year in [school_year, school_year + 1]:
            for day_off in calendar.holidays(year):
                begin = day_off[0]
                event = Event(day_off[1], begin)
                event.make_all_day()
                if event.begin > school_begin and event.begin < school_end:
                    # Remove 1s to end so that it does not overrides next day
                    event.end = event.end.shift(seconds=-1)
                    days_off_school.events.add(event)

        # Create timeline object
        timeline = days_off_school.timeline

        def get_last_tue(date):
            while date.weekday() != 1:
                date = date.shift(days=-1)
            return date

        def set_end(date):
            return date.replace(hour=16, minute=30, second=0, microsecond=0)

        # Now create dict of all days of school year and status
        # ordered by week number
        current = school_begin
        while int(current.strftime("%w")) > 1:
            current = current.shift(days=-1)
        while current < school_end:
            day = current.strftime("%d")
            week_number = current.isocalendar()[1]
            if week_number not in school_calendar.keys():
                school_calendar[week_number] = []
                current_week = school_calendar[week_number]

            # Limite cantine
            limit = set_end(
                get_last_tue(
                    current.shift(weeks=-1) if current.weekday() >= 1 else current
                )
            )
            past_cantine = arrow.now() > limit
            past_garderie = current < arrow.now()
            month = current.strftime("%B").capitalize()
            data = {"day": day, "month": month, "date": current.strftime("%Y%m%d")}
            # If one of these is past, then save immediately
            data["bookable_cantine"] = not past_cantine
            data["bookable_garderie"] = not past_garderie
            if not data["bookable_cantine"] and not data["bookable_garderie"]:
                current_week.append(data)
                current = current.shift(days=+1)
                continue
            if current.isoweekday() in NON_WORKING_DAYS or current.isoweekday() in [
                6,
                7,
            ]:
                data["bookable_cantine"] = False
                data["bookable_garderie"] = False
                data["bookable"] = False
                current_week.append(data)
            elif len([i for i in timeline.at(current)]) > 0:
                data["bookable_cantine"] = False
                data["bookable_garderie"] = False
                data["bookable"] = False
                current_week.append(data)
            elif current < school_begin:
                data["bookable_cantine"] = False
                data["bookable_garderie"] = False
                data["bookable"] = False
                current_week.append(data)
            else:
                data["bookable"] = True
                current_week.append(data)
            current = current.shift(days=+1)
        # Create set of periods
        i = 1
        periods = {
            i: {
                "begin": school_begin.format("YYYYMMDD"),
                "begin_pretty": school_begin.format("DD/MM/YYYY"),
            }
        }
        for event in sorted(edu_calendar.events):
            if event.begin < school_begin:
                continue
            if event.begin > school_end:
                continue
            if "Vacances" in event.name:
                periods[i]["end"] = event.begin.format("YYYYMMDD")
                periods[i]["end_pretty"] = event.begin.format("DD/MM/YYYY")
                i += 1
                periods[i] = {
                    "begin": event.end.format("YYYYMMDD"),
                    "begin_pretty": event.end.format("DD/MM/YYYY"),
                }
        periods.pop(i)
        self.periods = periods
        self.calendar = school_calendar
