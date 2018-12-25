# -*- coding: utf-8 -*-
# TODO: TRANSLATE HOLE FILE AND IMPROVE CODE
import datetime
import re
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from sqlite3 import IntegrityError
from typing import List

from bs4 import BeautifulSoup as Soup

from rpi.connections import Connections
from rpi.dns import RpiDns
from rpi.downloader import Downloader
from rpi.exceptions import InvalidMonthError, InvalidDayError, DownloaderError
from rpi.launcher import BaseMinimalLauncher
from rpi.managers.user_manager import UserManager
from rpi.rpi_logging import Logger

MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre")
DIAS = ("lunes", "martes", "miercoles", "jueves",
        "viernes", "sabado", "domingo")
TDIAS = ("lunes", "martes", "miércoles", "jueves",
         "viernes", "sábado", "domingo")
EDIAS = ('MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY')
MESES_MAX = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
PARAMETROS = ("--tomorrow", "--t", "--find", "--f", "--yesterday", "--y")

logger = Logger.get(__file__, __name__)

if int(time.strftime("%Y")) % 4 == 0:
    MESES_MAX[1] = 29


def extend_date(anything):
    """Extends a date or a set of dates of 01/01/2018 type into DIA: 01 de Enero de 2018 (Lunes)."""
    output = []
    if isinstance(anything, str):
        try:
            date_extended = _extend_date(anything)
            return date_extended
        except ValueError:
            return anything
    else:
        iterable = anything

    for element in iterable:
        date_extended = _extend_date(element)
        output.append(date_extended)

    return output


def _extend_date(date):
    """Extends a date of 01/01/2018 type into DIA: 01 de Enero de 2018 (Lunes)."""

    day, month, year = [int(x) for x in date.split('/')]

    date = datetime.datetime.strptime(f'{day}-{month}-{year}', '%d-%m-%Y').strftime('%A').upper()
    date = TDIAS[EDIAS.index(date)]
    string = f'DÍA: {day:02d} DE {MESES[month - 1].upper()} DE {year:04d} ({date.upper()})'
    return string


def get_date():
    """Returns the current day, month, and year."""
    p = datetime.date.today()
    return p.day, p.month, p.year


class MenusDatabaseManager:
    """Gestor de la base de datos de menús de la Residencia Santiago."""

    def __init__(self):
        logger.debug('Starting database manager')
        self.con = sqlite3.connect(RpiDns.get('sqlite.menus_resi'))
        self.cur = self.con.cursor()

        self.cur.execute("""CREATE TABLE IF NOT EXISTS "menus" (
                         id INTEGER PRIMARY KEY NOT NULL,
                         origin VARCHAR NOT NULL,
                         day_month INTEGER NOT NULL,
                         month INTEGER NOT NULL,
                         year INTEGER NOT NULL,
                         day_week VARCHAR,
                         lunch1 VARCHAR,
                         lunch2 VARCHAR,
                         dinner1 VARCHAR,
                         dinner2 VARCHAR)""")

        self.cur.execute("""CREATE TABLE IF NOT EXISTS "links" (
                        'datetime' VARCHAR NOT NULL,
                        'link' VARCHAR PRIMARY KEY NOT NULL                        
                        )""")
        self.con.commit()

    def __contains__(self, item):
        if isinstance(item, str) is False:
            raise TypeError('Only links are accepted (str).')

        return item in self.extract_links()

    # ------   OPERATIONS WITH LINKS   ------
    def save_link(self, link):
        """Saves a link in the database with the current datetime."""
        dia = datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        data_pack = (dia, link)

        try:
            self.cur.execute('INSERT INTO "links" VALUES(?,?)', data_pack)
        except IntegrityError:
            return False
        return True

    def extract_links(self):
        self.cur.execute("SELECT link FROM links")
        links = [x[0] for x in self.cur.fetchall()]
        return links

    # ------   OPERATIONS WITH MENUS   ------
    def save_menu(self, menu):
        """Saves a menu in the database."""
        datos = (
            menu.id, menu.origin, menu.month_day, menu.month_as_number, menu.year, menu.dia_semana, menu.comida_p1,
            menu.comida_p2,
            menu.cena_p1, menu.cena_p2)
        try:
            self.cur.execute('INSERT INTO "menus" VALUES(?,?,?,?,?,?,?,?,?,?)', datos)
        except IntegrityError:
            return False
        return True

    def save_changes(self):
        """Saves all changes in the databases."""
        self.con.commit()

    def extract_menus(self):
        """Extract all data from the database."""
        # todo: this method should return a list of Menus, not a list of chaos data.
        self.cur.execute('SELECT * FROM "menus"')
        return self.cur.fetchall()

    def close(self):
        """Saves changes and closes the database connection."""
        self.con.commit()
        self.con.close()
        del self.con
        del self.cur


@dataclass
class Menu:
    """Represents the different meals of a determined day."""
    day: int
    month: int
    year: int

    origin: str = 'auto'
    day_of_week_as_str: str = None
    launch1: str = None
    launch2: str = None
    dinner1: str = None
    dinner2: str = None

    month_as_str: str = field(init=False)

    def __post_init__(self):

        if not 1 <= self.month <= 12:
            raise InvalidMonthError(f"{self.month} is not a valid month [1-12]")

        self.month_as_str = MESES[self.month - 1]

        if self.day_of_week_as_str is None:
            foo = datetime.datetime(self.year, self.month, self.day).strftime('%A').upper()
            self.day_of_week_as_str = TDIAS[EDIAS.index(foo)].capitalize()

    @property
    def id(self):
        """Returns the id of a menu, formed by year, month and day."""
        return int(f'{self.year:04d}{self.month:02d}{self.day:02d}')

    @property
    def date(self):
        """Returns the date of the menu as an instance of datetiem.date"""
        return datetime.date(self.year, self.month, self.day)

    @staticmethod
    def generate_id(dia_mes, mes, ano):
        """Genera la id de un menú."""
        return int(f'{ano:04d}{mes:02d}{dia_mes:02d}')

    def __str__(self, arg='default', html=False, minimal=False):

        if minimal is True and arg == 'default':
            logger.warning('Too much information (minimal=True, arg=\'default\')')

        o = ''
        if html is True:
            o += '<b>'
        if minimal is False:
            o += "{} de {} de {} ({}):".format(
                self.day, self.month, self.year, self.day_of_week_as_str)
        if html is True:
            o += '</b>'

        if minimal is False:
            o += '\n'

        if arg == 'comida' or arg == 'default':
            if self.launch1 is not None:
                o += f'Comida: {self.launch1}'
                if self.launch2 is not None:
                    o += f' y {self.launch2}'

        if arg == 'default':
            o += '\n'

        if arg == 'cena' or arg == 'default':
            if self.dinner1 is not None:
                o += f'Cena: {self.dinner1}'
                if self.dinner2 is not None:
                    o += f' y {self.dinner2}'

        return o

    # def __repr__(self):
    #     o = []
    #     if self.day:
    #         o.append(f"{repr(self.day)}")
    #     if self.month:
    #         o.append(f"{repr(self.month)}")
    #     if self.year:
    #         o.append(f"{repr(self.year)}")
    #     if self.day_of_week_as_str:
    #         o.append(f"day_of_week_as_str='{self.day_of_week_as_str}'")
    #     if self.launch1:
    #         o.append(f"launch1='{self.launch1}'")
    #     if self.launch2:
    #         o.append(f"launch2='{self.launch2}'")
    #     if self.dinner1:
    #         o.append(f"dinner1='{self.dinner1}'")
    #     if self.dinner2:
    #         o.append(f"dinner2='{self.dinner2}'")
    #     return "Menu(" + ", ".join(o) + ')'

    # def __lt__(self, other):
    #     iself = None
    #     iother = None
    #     for i in range(len(MESES)):
    #         if MESES[i] == self.month:
    #             iself = i
    #
    #     for i in range(len(MESES)):
    #         if MESES[i] == other.month:
    #             iother = i
    #
    #     if iself is None:
    #         raise InvalidMonthError("{} is not a month".format(self.month))
    #     if iother is None:
    #         raise InvalidMonthError("{} is not a month".format(other.month))
    #
    #     if iself != iother:
    #         return iself < iother
    #     else:
    #         return self.day < other.dia_mes

    # def __ge__(self, other):
    #     return self.date >= other.date


class MenusManager(object):
    """Manages a list of menus."""

    def __init__(self):
        logger.debug('Starting menus manager')

        self.list = []
        self.opcodes = []
        self.downloader = Downloader()
        self.database_manager = MenusDatabaseManager()

        # Patterns:
        # 1. Detects "DÍA: 28 DE JUNIO DE 2018 (JUEVES)".
        # 2. Detects "28/06/2018".
        # 3. Detects "27. junio 2018" (unused).
        # 4. Detects when "1ER PLATO" is splitted from the dinner itself (or the 2nd) [I dont understand this...]
        # 5. Detects when there are no dinner plates, and takes until dessert.

        self.pattern1 = re.compile(r'DÍA:\s\d{2}\sDE\s[a-zA-Z]{4,10}\sDE\s\d{4}\s\(\w{5,9}\)', re.IGNORECASE)
        self.pattern2 = re.compile(r'\d{2}/\d{2}/\d{4}', re.IGNORECASE)
        # self.pattern3 = re.compile(r'\d{2}\.\s[a-zA-Z]{4,10}\s\d{4}', re.IGNORECASE)
        self.pattern4 = re.compile(r'((1ER|2º)\sPLATO:\${3}[\w\s]*)', re.IGNORECASE)
        self.pattern5 = re.compile(r'(?<=CENA:\${3})(?!(1ER))[\w\s.:,;$]+(?=\${3}POSTRE)', re.IGNORECASE)

        self.opcodes_lock = threading.Lock()
        self.sqlite_lock = threading.Lock()
        self.links_to_save = []

    def __contains__(self, item):
        if isinstance(item, int):
            return item in (x.id for x in self)
        else:
            raise TypeError('ID must be an integer')

    def __iter__(self):
        return iter(self.list)

    def load_from_database(self):

        logger.debug('Loading menus from database')
        menus = self.database_manager.extract_menus()
        for row in menus:
            _, _, day, month, year, day_of_wee_as_str, launch1, launch2, dinner1, dinner2 = row
            menu = Menu(
                day=day, month=month, year=year, day_of_week_as_str=day_of_wee_as_str,
                launch1=launch1, launch2=launch2, dinner1=dinner1, dinner2=dinner2
            )
            self.list.append(menu)

    def save_to_database(self):
        logger.debug('Saving to database')
        i = 0
        for menu in self:
            out = self.database_manager.save_menu(menu)
            if out:
                i += 1
        self.database_manager.save_changes()
        return i

    def sort(self, **kwargs):
        self.list.sort(**kwargs)

    def update(self, day, month, year, **kwargs):
        possible_days = [x for x in self.list if x.dia_mes == day]

        for x in possible_days:
            if x.mes == month and x.ano == year:
                index = self.list.index(x)

                if "day_of_week_as_str" in kwargs:
                    x.dia_semana = kwargs.pop("day_of_week_as_str")
                if "launch1" in kwargs:
                    x.comida_p1 = kwargs.pop("launch1")
                if "launch2" in kwargs:
                    x.comida_p2 = kwargs.pop("launch2")
                if "dinner1" in kwargs:
                    x.cena_p1 = kwargs.pop("dinner1")
                if "dinner2" in kwargs:
                    x.cena_p2 = kwargs.pop("dinner2")
                self.list[index] = x
                break
        else:
            menu = Menu(day, month, year)

            if "day_of_week_as_str" in kwargs:
                menu.day_of_week_as_str = kwargs.pop("day_of_week_as_str")
            if "launch1" in kwargs:
                menu.launch1 = kwargs.pop("launch1")
            if "launch2" in kwargs:
                menu.launch2 = kwargs.pop("launch2")
            if "dinner1" in kwargs:
                menu.dinner1 = kwargs.pop("dinner1")
            if "dinner2" in kwargs:
                menu.dinner2 = kwargs.pop("dinner2")
            self.list.append(menu)

    @classmethod
    def load(cls, url):
        self = object.__new__(cls)
        self.__init__()
        self.load_from_database()

        current_day, current_month, current_year = get_date()

        current_id = Menu.generate_id(current_day, current_month, current_year)

        if current_id in self:
            return self
        self.download_and_process_web(url)
        self.save_to_database()

        return self

    @staticmethod
    def load_csv(csvpath):
        """Genera los menús a partid de un archivo csv separado por ; Ej: 31;12;2018;launch1;launch2...'"""
        self = object.__new__(MenusManager)
        self.__init__()
        with open(csvpath, encoding='utf-8') as f:
            contenido = f.read().splitlines()

        contenido = [x.split(';') for x in contenido]
        contenido = [[elemento.strip() for elemento in fila] for fila in contenido]
        cont1 = ['a', 'al', 'la', 'ante', 'bajo', 'con', 'contra', 'de', 'del', 'desde', 'durante', 'en', 'hacia',
                 'hasta', 'mediante', 'o', 'para', 'por', 'según', 'sin', 'sobre', 'tras', 'y']
        titled = [' ' + x.title() + ' ' for x in cont1]
        cont1 = [' ' + x + ' ' for x in cont1]
        copia = []

        for fila in contenido:
            copia_fila = []
            if 'day' in fila:
                continue
            for elemento in fila:
                elemento = elemento.title()
                for i in range(len(cont1)):
                    elemento = elemento.replace(titled[i], cont1[i])
                try:
                    elemento = int(elemento)
                except ValueError:
                    pass
                copia_fila.append(elemento)
            copia.append(copia_fila)

        contenido = copia

        for fila in contenido:
            logger.debug('Añadiendo menú manual: ' + str(fila))
            self.list.append(Menu(fila[0], fila[1], fila[2], launch1=fila[3], launch2=fila[4],
                                  dinner1=fila[5], dinner2=fila[6], origin='manual'))

        guardado = self.save_to_database()
        logger.debug(f'Guardados {guardado} registros en la base de datos')
        return guardado

    def download_and_process_web(self, url):
        """Descarga y procesa la página web."""
        opcodes = self.generate_opcodes(url)
        if opcodes == -1:
            return -1
        lista = self.process_opcodes()

        cont1 = ['a', 'al', 'ante', 'bajo', 'con', 'contra', 'de', 'del',
                 'desde', 'durante', 'en', 'hacia', 'hasta', 'mediante', 'o',
                 'para', 'por', 'según', 'sin', 'sobre', 'tras', 'y']

        titled = [' ' + x.title() + ' ' for x in cont1]

        for e in lista:
            ano = int(e['year'])
            mes = MESES[e['month_as_str'] - 1]
            dia = int(e['dia'])
            code = e['code']
            value = e['value']

            for k in titled:
                if k in value:
                    value = value.replace(k, k.lower())

            value = value.replace(" Y ", " y ")
            value = value.replace(" A ", " a ")
            value = value.replace(" Al ", " al ")
            value = value.replace(" De ", " de ")
            value = value.replace(" La ", " la ")
            value = value.replace(" Con ", " con ")

            if code == "xx":
                self.update(dia, mes, ano, dia_semana=value)
            elif code == "L1":
                self.update(dia, mes, ano, comida_p1=value)
            elif code == "L2":
                self.update(dia, mes, ano, comida_p2=value)
            elif code == "D1":
                self.update(dia, mes, ano, cena_p1=value)
            elif code == "D2":
                self.update(dia, mes, ano, cena_p2=value)

        return self

    def generate_opcodes(self, url):
        """Descarga la web de la residencia y crea los opcodes."""

        try:
            html = self.downloader.get(url)
        except DownloaderError:
            return -1

        sopa = Soup(html.text, "html.parser")
        containers = sopa.findAll("div", {"class": "j-blog-meta"})

        urls = []
        text = []
        for container in containers:
            text.append(container.text)
            urls.append(container.a['href'])

        hilos = []
        i = 1
        for url in urls:
            if url in self.database_manager:
                continue
            hilo = threading.Thread(name=str(i), target=self.procesar_url_menus, args=(url,))
            hilo.start()
            hilos.append(hilo)
            i += 1

        for hilo in hilos:
            hilo.join()

        for enlace in self.links_to_save:
            self.database_manager.save_link(enlace)

    def append_to_opcodes(self, anything):
        with self.opcodes_lock:
            self.opcodes.append(anything)

    def procesar_url_menus(self, url):

        try:
            html = self.downloader.get(url)
        except DownloaderError:
            logger.error('Skipped: ' + url)
            return

        with self.sqlite_lock:
            self.links_to_save.append(url)
        sopa = Soup(html.text, "html.parser")

        resultado = sopa.find('article', {'class': 'j-blog'})
        textos = resultado.text.split('\n')

        for i in range(len(textos)):
            textos[i] = textos[i].strip().replace('\xa0', '')
        while '' in textos:
            textos.remove('')

        todo_junto = '$$$'.join(textos)

        for match in self.pattern4.finditer(todo_junto):
            original = match.group(0)
            cambio = original.replace('$$$', ' ')
            todo_junto = todo_junto.replace(original, cambio)

        for match in self.pattern5.finditer(todo_junto):
            original = match.group(0)
            cambio = '1ER PLATO: ' + original.replace('$$$', ' ')
            todo_junto = todo_junto.replace(original, cambio)

        textos = todo_junto.split('$$$')

        total = ' '.join(textos)
        matches1 = self.pattern1.findall(total)
        matches2 = self.pattern2.findall(total)
        matches = matches1 + extend_date(matches2)

        data = dict()
        data['comida'] = False
        data['dia'] = False
        data['cena'] = False
        for elem in textos:
            elem = elem.replace('\t', ' ')
            elem = elem.replace('\r', ' ')
            elem = elem.replace('\xa0', ' ')
            elem = elem.replace('    ', ' ')
            elem = elem.replace('   ', ' ')
            elem = elem.replace('  ', ' ')
            elem = elem.replace(' ', ' ')
            elem = elem.replace('_', ' ')

            while elem[0] == ' ':
                elem = elem[1:]
                if len(elem) == 0:
                    break

            if len(elem) == 0:
                continue

            if self.pattern2.match(elem):
                elem = extend_date(elem)

            if elem.count("DÍA:"):
                for match in matches:
                    if elem in match:
                        elem = match
                        break
                dia_mes = elem[5:7]
                for i in range(len(MESES)):
                    if elem.lower().count(MESES[i]):
                        index_meses = i
                        break
                else:
                    continue
                mes = MESES[index_meses]
                ano = elem[15 + len(mes):19 + len(mes)]
                dia_mes, ano = [int(x) for x in [dia_mes, ano]]

                for i in range(len(DIAS)):
                    if elem.lower().count(DIAS[i]) != 0:
                        index_dias = i
                        break
                else:
                    for i in range(len(TDIAS)):
                        if elem.lower().count(TDIAS[i]) != 0:
                            index_dias = i
                            break
                    else:
                        raise InvalidDayError(f'Error en el día: {elem}')
                dia_semana = TDIAS[index_dias].title()

                elem = (f"{ano:04d}{index_meses + 1:02d}{dia_mes:02d}xx"
                        f" {dia_semana}")
                data['dia'] = True
                data['dia_real'] = (
                    f"{ano:04d}{index_meses + 1:02d}{dia_mes:02d}")
                data['comida'] = False
                data['cena'] = False
                self.append_to_opcodes(elem)
                continue

            if elem.count("COMIDA"):
                data['comida'] = True
                continue

            if elem.count("BUFFET"):
                continue

            if elem.count("DESAYUNO"):
                continue

            if elem.count("CENA"):
                data['cena'] = True
                continue

            if elem.count("TUMACA, EMBUTIDO"):
                continue

            if elem.count("MANTEQUILLA, MERMELADA"):
                continue

            if elem.count("POSTRE"):
                continue

            if elem.lower().count('tag'):
                continue

            if elem.count("1ER PLATO: "):
                try:
                    if data['cena']:
                        self.append_to_opcodes(f"{data['dia_real']}D1 " + elem[11:])
                    elif data['comida']:
                        self.append_to_opcodes(f"{data['dia_real']}L1 " + elem[11:])
                except IndexError:
                    pass
                continue

            if elem.count("2º PLATO: "):
                try:
                    if data['cena']:
                        self.append_to_opcodes(f"{data['dia_real']}D2 " + elem[10:])
                    elif data['comida']:
                        self.append_to_opcodes(f"{data['dia_real']}L2 " + elem[10:])
                except IndexError:
                    pass
                continue

        return

    def process_opcodes(self) -> List[dict]:
        """Transforma una list del tipo [OPCODE] [VALOR] en una list con la información de cada opcode extraída en
        forma de diccionario."""
        salida = []
        for line in self.opcodes:
            d = {}
            opcode = line[:10]
            value = line[11:].title()

            ano = int(opcode[:4])
            mes = int(opcode[4:6])
            dia = int(opcode[6:8])
            code = opcode[8:10]

            if code == 'xx':
                value = value.capitalize()

            d['year'] = ano
            d['month_as_str'] = mes
            d['dia'] = dia
            d['code'] = code
            d['value'] = value
            salida.append(d)

        return salida

    def week_to_str(self, today):
        p = ''
        counter = 0
        level = today - datetime.timedelta(days=7)
        for menu in self:
            if today >= menu.date >= level:
                counter += 1
                p += menu.__str__(html=True)
                p += '\n\n'
        if counter == 0:
            return False
        return p

    @staticmethod
    def notify(message, destinations, show='default'):
        title = 'Menús Resi'
        gu = UserManager()

        if isinstance(destinations, str):
            if destinations.lower() == 'all':
                destinations = gu.usernames

        if isinstance(message, Menu):
            mensaje_normal = message.__str__(arg=show)
            mensaje_minimal = message.__str__(arg=show, minimal=True)
        else:
            mensaje_minimal = message
            mensaje_normal = message

        if isinstance(destinations, str):
            usuario = gu.get_by_username(destinations).username
            if isinstance(usuario.launcher, BaseMinimalLauncher):
                Connections.notify(title, mensaje_minimal, destinations=usuario, file=__file__)
            else:
                Connections.notify(title, mensaje_normal, destinations=usuario, file=__file__)
        else:
            try:
                usuarios_normales = []
                usuarios_minimal = []
                for nombre in destinations:
                    usuario = gu.get_by_username(nombre)
                    if isinstance(usuario.launcher, BaseMinimalLauncher):
                        usuarios_minimal.append(usuario.username)
                    else:
                        usuarios_normales.append(usuario.username)
                Connections.notify(title, mensaje_normal, destinations=usuarios_normales, file=__file__)
                Connections.notify(title, mensaje_minimal, destinations=usuarios_minimal, file=__file__)
            except TypeError:
                raise TypeError(
                    '"destinations" debe ser str o iterable, no ' + type(destinations).__name__)
