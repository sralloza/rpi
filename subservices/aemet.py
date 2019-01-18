# -*- coding: utf-8 -*-

import datetime
import logging
from dataclasses import dataclass, field

from bs4 import BeautifulSoup as Soup

from rpi.custom_logging import configure_logging
from rpi.downloader import Downloader
from rpi.exceptions import DownloaderError

configure_logging(called_from=__file__, use_logs_folder=True)


@dataclass()
class WeatherRegistry:
    """Represents a weather registry of one hour."""
    day_of_week: str = field(repr=False)
    day: int
    hour: int
    temperature: int
    thermal_sensation: int
    wind_direction: int = field(repr=False)
    wind_speed: int = field(repr=False)
    wind_speed_max: int = field(repr=False)
    rain_mm: int
    snow_mm: int
    rel_hum: float
    rain_prob: float
    snow_prob: float
    storm_prob: float
    announcements: str = field(repr=False)
    info: str = field(repr=False)
    _args: tuple = field(init=False, repr=False)


def __post_init__(self):
    self._args = (
        self.day_of_week, self.day, self.hour, self.temperature, self.thermal_sensation,
        self.wind_direction, self.wind_speed, self.wind_speed_max, self.rain_mm, self.snow_mm,
        self.rel_hum, self.rain_prob, self.snow_prob,
        self.storm_prob, self.announcements, self.info,
    )


def strfdata(self):
    """Returns the registry formatted as a readable string."""

    return (f"[{self.dia_semana},{self.dia_mes:2d}][] "
            f"\n-{self.temp:2d}ºC ({self.sens_term:2d} ºC)\n-"
            f"Viento: {self.viento} Km/h ({self.viento_direc})\n-"
            f"Probabilidades: {self.prob_lluvia:>4s} de lluvia, "
            f"{self.prob_nieve:>4s} de nieve y {self.prob_tormenta:>4s} "
            f"de tormenta\n-Cantidades    : {self.lluvia_mm:>4.1f} mm "
            f"lluvia, {self.nieve_mm:>4.1f} mm nieve\n-({self.info})\n")


class WeatherRecordsManager:
    """Represents a set of wheater records."""
    SEMANA = ('Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo')

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.list = []

    def __len__(self):
        return len(self.list)

    def __getitem__(self, index):
        return self.list[index]

    def __iter__(self):
        return iter(self.list)

    @classmethod
    def valladolid(cls):
        return cls.procesar(
            url='http://www.aemet.es/es/eltiempo/prediccion/'
                'municipios/horas/tabla/valladolid-id47186')

    @classmethod
    def procesar(cls, url):
        """Processes an AEMET web page to extract the hour prevision."""

        self = cls.__new__(cls)
        self.__init__()

        self.logger.debug(f'Processing web - {url!r}')

        try:
            with Downloader() as downloader:
                principal_page = downloader.get(url)
        except DownloaderError:
            self.logger.critical('Aemet download error')
            return None

        s = Soup(principal_page.text, "html.parser")
        rows = s.findAll(
            "tr", {"class": "fila_hora cabecera_niv2"})

        day_of_week = "Error"
        day = -1
        rain_prob = None
        snow_prob = None
        storm_prob = None
        for row in rows:
            img = row.find("img")
            info = img['title']

            row = row.text.strip(' ')
            row = row.replace('\n', ' ')
            row = row.replace('\r', '')
            row = row.replace('\t', '')
            elements = row.split(" ")
            n_espacios = elements.count('')

            for counter in range(n_espacios):
                elements.remove('')

            try:
                _ = int(elements[0])
                del _

                elements.insert(0, day_of_week)
                elements.insert(1, day)
            except ValueError:
                if elements[0][:2] == "mi":
                    elements[0] = "mié"
                day_of_week = elements[0]
                day = elements[1]

            if elements[11].count('%'):
                rain_prob = elements[11]
                elements.pop(12)
                snow_prob = elements[12]
                elements.pop(13)
                storm_prob = elements[13]
                elements.pop(14)
            else:
                elements.insert(11, rain_prob)
                elements.insert(12, snow_prob)
                elements.insert(13, storm_prob)

            foo = ""
            for h in range(14, len(elements)):
                if h != 14:
                    foo += ' '
                foo += elements[h]
            elements[14] = foo

            for h in range(len(elements) - 15):
                elements.pop()

            elements.append(info)

            for foo in (1, 2, 3, 4, 6, 7, 10):
                elements[foo] = int(elements[foo])

            for foo in (8, 9):
                if elements[foo].lower() in ["lp", "ip"]:
                    elements[foo] = 0.0
                elements[foo] = float(elements[foo])

            self.list.append(WeatherRegistry(*elements))

        self.logger.debug('Web processed successfully')
        return self

    def mm(self, date: datetime.date, index=False):
        """Returns the sum of rain and snow in mm of a day."""

        mm_sum = 0
        counter = 0
        for register in self:
            if register.day == date.day:
                mm_sum += register.rain_mm
                mm_sum += register.snow_mm
                counter += 1

        self.logger.debug(f'milimiters for {date}: {mm_sum}, {counter}')

        if index is True:
            return mm_sum, counter

        return mm_sum

    def mean_probability_percentage(self, date: datetime.date, index=False):
        """Returns the mean of the sum of the probability of rain, storm and snow of a day."""

        percentage_sum = 0
        counter = 0
        for register in self:
            if register.day == date.day:
                percentage_sum += int(register.rain_prob.replace('%', ''))
                percentage_sum += int(register.snow_prob.replace('%', ''))
                percentage_sum += int(register.storm_prob.replace('%', ''))
                counter += 1

        if counter == 0:
            return -1

        percentage_mean = percentage_sum / counter
        if percentage_mean > 100:
            percentage_mean = 100.0

        self.logger.debug(f'Percentage mean for {date}: {percentage_mean}, {counter}')

        if index is True:
            return percentage_mean, counter

        return percentage_mean
