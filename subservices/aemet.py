# -*- coding: utf-8 -*-

import datetime
from dataclasses import dataclass, field

from bs4 import BeautifulSoup as Soup

from rpi.downloader import Downloader
from rpi.exceptions import DownloaderError
from rpi.rpi_logging import Logger

logger = Logger.get(__file__, __name__)


@dataclass()
class WeatherRegistry:
    """Represents a weather registry of one hour."""
    day_of_week: str = field(repr=False)
    month_day: int
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
        self.dia_semana, self.dia_mes, self.hora, self.temp, self.sens_term, self.viento_direc, self.viento,
        self.viento_max, self.lluvia_mm, self.nieve_mm, self.hum_rel, self.prob_lluvia, self.prob_nieve,
        self.prob_tormenta, self.avisos, self.info,
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


class GestorRegistros:
    """Represents a set of wheater records."""
    SEMANA = ('Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo')

    def __init__(self):
        self.lista = []

    def __len__(self):
        return len(self.lista)

    def __getitem__(self, index):
        return self.lista[index]

    def __iter__(self):
        return iter(self.lista)

    @classmethod
    def procesar(cls, url):
        """Procesa una página de AEMET para extraer la previsión por horas."""

        self = cls.__new__(cls)
        self.__init__()

        try:
            with Downloader() as downloader:
                principal_page = downloader.get(url)
        except DownloaderError:
            logger.critical('Error de descarga de aemet')
            return None

        sopa_principal = Soup(principal_page.text, "html.parser")
        filas = sopa_principal.findAll(
            "tr", {"class": "fila_hora cabecera_niv2"})

        dia_semana = "Error"
        dia_mes = "Error"
        prob_lluvia = None
        prob_nieve = None
        prob_tormenta = None
        for i in filas:
            img = i.find("img")
            info = img['title']

            fila = i.text.strip(' ')
            fila = fila.replace('\n', ' ')
            fila = fila.replace('\r', '')
            fila = fila.replace('\t', '')
            elems = fila.split(" ")
            n_espacios = elems.count('')

            for contador in range(n_espacios):
                elems.remove('')

            try:
                _ = int(elems[0])
                del _

                elems.insert(0, dia_semana)
                elems.insert(1, dia_mes)
            except ValueError:
                if elems[0][:2] == "mi":
                    elems[0] = "mié"
                dia_semana = elems[0]
                dia_mes = elems[1]

            if elems[11].count('%'):
                prob_lluvia = elems[11]
                elems.pop(12)
                prob_nieve = elems[12]
                elems.pop(13)
                prob_tormenta = elems[13]
                elems.pop(14)
            else:
                elems.insert(11, prob_lluvia)
                elems.insert(12, prob_nieve)
                elems.insert(13, prob_tormenta)

            foo = ""
            for h in range(14, len(elems)):
                if h != 14:
                    foo += ' '
                foo += elems[h]
            elems[14] = foo

            for h in range(len(elems) - 15):
                elems.pop()

            elems.append(info)

            for foo in (1, 2, 3, 4, 6, 7, 10):
                elems[foo] = int(elems[foo])

            for foo in (8, 9):
                if elems[foo].lower() in ["lp", "ip"]:
                    elems[foo] = 0.0
                elems[foo] = float(elems[foo])

            self.lista.append(WeatherRegistry(*elems))
        return self

    def mm(self, dia: datetime.date, index=False):
        """Devuelve la suma de lluvia y nieve en mm de un día."""
        dia_mes = dia.day

        suma = 0
        cont = 0
        for registro in self:
            if registro.dia_mes == dia_mes:
                suma += registro.lluvia_mm
                suma += registro.nieve_mm
                cont += 1

        if index is True:
            return suma, cont

        return suma

    def porcentaje_medio(self, dia: datetime.date, index=False):
        """Devuelve la suma de lluvia y nieve en mm de un día."""
        dia_mes = dia.day

        suma = 0
        cont = 0
        for registro in self:
            if registro.dia_mes == dia_mes:
                suma += int(registro.prob_lluvia.replace('%', ''))
                suma += int(registro.prob_nieve.replace('%', ''))
                suma += int(registro.prob_tormenta.replace('%', ''))
                cont += 1

        if cont == 0:
            return -1

        media = suma / cont
        if media > 100:
            media = 100.0

        if index is True:
            return media, cont

        return media
