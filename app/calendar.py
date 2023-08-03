import locale
from datetime import datetime, time, timedelta
from typing import Dict, List
import re

from icalendar import Calendar, Event, vText
from workalendar.europe import France

locale.setlocale(locale.LC_ALL, "fr_FR.UTF-8")
ZONE_B = r"Zones?.*B"
HOUR_LIMIT, MIN_LIMIT = (16, 30)
NO_CLASS = [2, 5, 6]


def getBookedData(booking_type, username=None):
    if booking_data := booking_type.query.filter(
        booking_type.username == username
    ).scalar():
        return booking_data.booked.split()
    else:
        return []


class CantinaCalendar:
    def __init__(
        self,
        year: int,
        location: vText = ZONE_B,
        ics_calendar: str = "Zone-A-B-C-Corse.ics",
    ) -> None:
        """Initialise le calendrier

        :param year: Année scolaire
        :type year: int
        :param location: Zone académique, defaults to ZONE_B
        :type location: vText, optional
        :param ics_calendar: Calendrier scolaire au format ICS, defaults to "Zone-A-B-C-Corse.ics"
        :type ics_calendar: str, optional
        """
        self.now = datetime.now()
        self.year = year
        self.location = location
        self.ics_calendar = ics_calendar
        self.events = self._get_zone_events(self._load_calendar_file())
        self.start = self._get_school_start()
        self.end = self._get_school_end()
        self.all_year = self._get_all_school_year()
        self.holidays = self._get_holidays()
        self.dt_periods = self._get_periods()
        self.periods = self._format_periods(self.dt_periods)
        self.bookable_cantine = self._list_bookable_cantine()
        self.bookable_garderie = self._list_bookable_garderie()
        self.calendar = self._create_calendar()

    def _load_calendar_file(self) -> Calendar:
        """Charge le fichier ICS

        :return: calendrier scolaire
        :rtype: Calendar
        """
        with open(self.ics_calendar, "rb") as calendar_file:
            return Calendar.from_ical(calendar_file.read())

    def _get_all_school_year(self) -> List[datetime]:
        """L'ensemble des dates de l'années scolaire, en commençant par un Lundi

        :return: liste des dates
        :rtype: List[datetime]
        """
        start = self.start
        while start.weekday() != 0:
            start -= timedelta(days=1)
        return self._get_date_range(start, self.end)

    def _is_in_period(self, event: Event) -> bool:
        """Définit si une date est dans une période donnée

        :param event: Evenement du calendrier
        :type event: Event
        :return: résultat
        :rtype: bool
        """
        start_date = event["DTSTART"].dt
        year = start_date.year
        month = start_date.month
        return (month >= 7 and year == self.year) or (
            month <= 7 and year == self.year + 1
        )

    def _check_location(self, event: Event) -> bool:
        """Vérifie si un évènement est dans la zone définie

        :param event: Evenement du calendrier
        :type event: Event
        :return: résultat
        :rtype: bool
        """
        return "LOCATION" in event.keys() and re.match(self.location, event["LOCATION"])

    def _get_zone_events(self, cal: Calendar) -> List[Event]:
        """Récupère les évènements liés à la zone définie

        :param cal: Calendrier
        :type cal: Calendar
        :return: liste des évènements
        :rtype: List[Event]
        """
        return [
            event
            for event in cal.subcomponents
            if self._check_location(event)
            and self._is_in_period(event)
            and "Enseignants" not in event["SUMMARY"]
        ]

    def _get_school_start(self) -> datetime:
        """Renvoie la date de la rentrée

        :return: date de la rentrée
        :rtype: datetime
        """
        return self.events[-1]["DTEND"].dt

    def _get_school_end(self) -> datetime:
        """Renvoie la date de fin des cours pour les élèves

        :return: date de fin
        :rtype: datetime
        """
        return self.events[0]["DTSTART"].dt

    def _get_feries(self) -> List[datetime]:
        """Renvoie la liste des jours fériés de l'année x et de l'année x +1

        :return: liste des jours fériés
        :rtype: List[datetime]
        """
        days = []
        for year in (self.year, self.year + 1):
            days += [_[0] for _ in France().holidays(year)]
        self.feries = days
        return days

    def _get_non_class_days(self) -> List[datetime]:
        """Renvoie la liste des jours sans classe
        (par exemple, Mercredi, Samedi et Dimanche)

        :return: liste des jours sans classe
        :rtype: List[datetime]
        """
        return [_ for _ in self.all_year if _.weekday() in NO_CLASS]

    def _get_off_days(self) -> List[datetime]:
        """Renvoie la liste complète des jours sans classe et fériés

        :return: jours non travaillés
        :rtype: List[datetime]
        """
        return self._get_feries() + self._get_non_class_days()

    def _get_date_range(self, start: datetime, end: datetime) -> List[datetime]:
        """Renvoie toutes les dates entre start et end

        :param start: date de début
        :type start: datetime
        :param end: date de fin
        :type end: datetime
        :return: liste des dates
        :rtype: List[datetime]
        """
        return [start + timedelta(days=x) for x in range((end - start).days + 1)]

    def _get_holidays(self) -> List[datetime]:
        """Renvoie toutes les dates non travaillées

        :return: liste des dates
        :rtype: List[datetime]
        """
        holidays = []
        for holiday in self.events:
            holidays += self._get_date_range(
                holiday["DTSTART"].dt,
                holiday["DTEND"].dt - timedelta(days=1)
                if holiday["DTEND"]
                else holiday["DTSTART"].dt - timedelta(days=1),
            )
        holidays += self._get_off_days()
        holidays = sorted(list(set(holidays)))
        # holidays.remove(rentree)
        return holidays

    def _pretty_date(self, date: datetime, format: str = r"%d/%m/%Y") -> str:
        """Renvoie la date au format DD/MM/YYYY

        :param date: date
        :type date: datetime
        :param format: format de date, defaults to r"%d/%m/%Y"
        :type format: str, optional
        :return: date
        :rtype: str
        """
        return date.strftime(format)

    def _basic_date(self, date: datetime, format: str = r"%Y%m%d") -> str:
        """Renvoie la date au format YYYYMMDD

        :param date: date
        :type date: datetime
        :param format: format de date, defaults to r"%Y%m%d"
        :type format: str, optional
        :return: date
        :rtype: str
        """
        return date.strftime(format)

    def _format_month(self, date: datetime) -> str:
        """Renvoie le mois au format long et en Français
        Janvier, Février etc...

        :param date: date
        :type date: datetime
        :return: nom du mois
        :rtype: str
        """
        return date.strftime(r"%B").capitalize()

    def _format_periods(self, periods: dict) -> dict:
        """Formate les périodes dans un dictionnaire

        :param periods: dictionnaire des périodes au format datetime
        :type periods: dict
        :return: dictionnaire formaté
        :rtype: dict
        """
        return {
            period: {
                "begin": self._basic_date(periods[period][0]),
                "begin_pretty": self._pretty_date(periods[period][0]),
                "end": self._basic_date(periods[period][-1]),
                "end_pretty": self._pretty_date(periods[period][-1]),
            }
            for period in periods
            if periods[period]
        }

    def _get_periods(self):
        periods = {0: []}
        period = 0
        in_holiday = False
        for day in self.all_year:
            if day not in self.holidays:
                in_holiday = False
                periods[period].append(day)
            elif day.weekday() not in NO_CLASS and day not in self.feries:
                if not in_holiday:
                    period += 1
                    periods[period] = []
                    in_holiday = True
        return periods

    def _get_week_number(self, date: datetime) -> str:
        return str(date.isocalendar()[1])

    def _init_calendar(self) -> Dict[str, list]:
        return {
            week_number: []
            for week_number in [self._get_week_number(_) for _ in self.all_year]
        }

    def _next_tue(self) -> datetime:
        date = self.now
        if date.weekday() == 1 and date.time() > time(HOUR_LIMIT, MIN_LIMIT):
            date = date + timedelta(days=1)
        while date.weekday() != 1:
            date = date + timedelta(days=1)
        return date

    def _set_time(
        self, date: datetime, hour: int = HOUR_LIMIT, minute: int = MIN_LIMIT
    ) -> datetime:
        return datetime.combine(date, time(hour, minute))

    def _define_cantine_limit_reservation(self) -> datetime:
        return self._set_time(self._next_tue())

    def _adjust_workdays(self, workdays):
        add = [
        ]
        for d in add:
            if d > self.now.date():
                workdays.append(d)
        # l.remove(date(2023, 5, 19))
        return workdays

    def _list_bookable_cantine(self):
        limit = self._define_cantine_limit_reservation()
        starting_day = (limit + timedelta(days=6)).date()
        workdays = [
            _ for _ in self.all_year if _ >= starting_day and _ not in self.holidays
        ]
        return self._adjust_workdays(workdays)

    def _is_bookable_cantine(self, date: datetime) -> bool:
        return date in self.bookable_cantine

    def _list_bookable_garderie(self):
        workdays = [
            _
            for _ in self.all_year
            if _ > self.now.date()
            if _ > self.now.date() and _ not in self.holidays
        ]
        return self._adjust_workdays(workdays)

    def _is_bookable_garderie(self, date: datetime) -> bool:
        return date in self.bookable_garderie

    def _define_day_parameters(self, date: datetime) -> Dict:
        return {
            "day": str(date.day),
            "month": self._format_month(date),
            "date": self._basic_date(date),
            "bookable_cantine": self._is_bookable_cantine(date),
            "bookable_garderie": self._is_bookable_garderie(date),
        }

    def _create_calendar(self) -> Dict[str, list]:
        calendar = self._init_calendar()
        for date in self.all_year:
            week_number = self._get_week_number(date)
            calendar[week_number].append(self._define_day_parameters(date))
        return calendar
