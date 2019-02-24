# -*- coding: utf-8 -*-
# TODO: TRANSLATE HOLE FILE AND IMPROVE CODE
import datetime
import logging
import re
import sqlite3
import threading
from dataclasses import dataclass, field
from typing import List, Union, Iterable

from bs4 import BeautifulSoup as Soup

from rpi.custom_logging import configure_logging
from rpi.dns import RpiDns
from rpi.downloader import Downloader
from rpi.exceptions import InvalidMonthError, InvalidDayError, DownloaderError

configure_logging(called_from=__file__, use_logs_folder=True)

MONTHS = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
          "agosto", "septiembre", "octubre", "noviembre", "diciembre")
DAYS = ("lunes", "martes", "miercoles", "jueves",
        "viernes", "sabado", "domingo")
ACCENT_DAYS = ("lunes", "martes", "miércoles", "jueves",
               "viernes", "sábado", "domingo")
ENGLISH_DAYS = ('MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY')


def extend_date(anything: Union[Iterable[str], str]):
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


def _extend_date(date: str) -> str:
    """Extends a date of 01/01/2018 type into DIA: 01 de Enero de 2018 (Lunes)."""

    day, month, year = [int(x) for x in date.split('/')]

    date = datetime.datetime.strptime(f'{day}-{month}-{year}', '%d-%m-%Y').strftime('%A').upper()
    date = ACCENT_DAYS[ENGLISH_DAYS.index(date)]
    string = f'DÍA: {day:02d} DE {MONTHS[month - 1].upper()} DE {year:04d} ({date.upper()})'
    return string


def get_date():
    """Returns the current day, month, and year."""
    today = datetime.date.today()
    return today.day, today.month, today.year


class MenusDatabaseManager:
    """Database manager for the menus"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.debug('Starting database manager')
        self.con = sqlite3.connect(RpiDns.get('sqlite.menus_resi'))
        self.cur = self.con.cursor()

        self.cur.execute("""CREATE TABLE IF NOT EXISTS "menus" (
                         id INTEGER PRIMARY KEY NOT NULL,
                         origin VARCHAR NOT NULL,
                         day_month INTEGER NOT NULL,
                         month INTEGER NOT NULL,
                         year INTEGER NOT NULL,
                         day_week VARCHAR,
                         launch1 VARCHAR,
                         launch2 VARCHAR,
                         dinner1 VARCHAR,
                         dinner2 VARCHAR)""")

        self.cur.execute("""CREATE TABLE IF NOT EXISTS "links" (
                        'datetime' VARCHAR NOT NULL,
                        'link' VARCHAR PRIMARY KEY NOT NULL                        
                        )""")

        self.cur.execute("""CREATE TABLE IF NOT EXISTS "updates" (
                        'datetime' PRIMARY KEY     
                        )""")

        self.con.commit()

    def __contains__(self, item):
        if isinstance(item, str) is False:
            raise TypeError('Only links are accepted (str).')

        return item in self.extract_links()

    # ------   OPERATIONS WITH UPDATES ------
    def set_update(self):
        """Sets the last update the actual datetime in the database."""

        now = datetime.datetime.today()
        try:
            if self.get_update() == datetime.datetime.min:
                self.cur.execute("insert into updates values(?)", (now.strftime('%y-%m-%d %H:%M:%S'),))
            else:
                self.cur.execute("update updates set datetime=?", (now.strftime('%y-%m-%d %H:%M:%S'),))
        except sqlite3.OperationalError:
            self.logger.critical('Operational Error')
            self.logger.exception('')
        self.con.commit()
        return True

    def get_update(self) -> datetime.datetime:
        """Gets the datetime of the last update."""

        self.cur.execute("select datetime from updates")
        try:
            result = datetime.datetime.strptime(self.cur.fetchone()[0], '%y-%m-%d %H:%M:%S')
        except TypeError:
            return datetime.datetime.min
        return result

    # ------   OPERATIONS WITH LINKS   ------
    def save_link(self, link: str):
        """Saves a link in the database with the current datetime.

        Args:
            link (str): link to save in the database.
        """

        dia = datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        data_pack = (dia, link)

        try:
            self.cur.execute('INSERT INTO "links" VALUES(?,?)', data_pack)
        except sqlite3.IntegrityError:
            self.logger.debug('Link already exists: %r', link)
            return False

        self.logger.debug('Saved link: %r', link)
        return True

    def extract_links(self):
        """Returns the links saved in the database."""
        self.logger.debug('Extracting links from database')
        self.cur.execute("SELECT link FROM links")

        return tuple(x[0] for x in self.cur.fetchall())

    # ------   OPERATIONS WITH MENUS   ------
    def save_menu(self, menu) -> bool:
        """Saves a menu in the database.

        Args:
            menu (Menu): Menu to save in the database.

        Returns:
            bool: Status of the operation.
        """
        datos = (
            menu.id, menu.origin, menu.day, menu.month, menu.year, menu.day_of_week_as_str,
            menu.launch1,
            menu.launch2, menu.dinner1, menu.dinner2)
        try:
            self.cur.execute('INSERT INTO "menus" VALUES(?,?,?,?,?,?,?,?,?,?)', datos)
        except sqlite3.IntegrityError:
            return False
        self.logger.debug('Saved menu: %r', menu)
        return True

    def save_changes(self):
        """Saves all changes in the databases."""
        self.con.commit()

    def extract_menus_data(self) -> tuple:
        """Extract all data from the database."""
        self.cur.execute('SELECT * FROM "menus"')
        self.logger.debug('Extracting menus data from database')
        return tuple(self.cur.fetchall())

    def close(self):
        """Saves changes and closes the database connection."""
        self.logger.debug('Closing database')
        self.con.commit()
        self.con.close()


@dataclass
class Menu:
    """Represents the different meals of a determined day."""
    day: int
    month: int
    year: int

    origin: str = 'auto'
    launch1: str = None
    launch2: str = None
    dinner1: str = None
    dinner2: str = None

    day_of_week_as_str: str = field(init=False)
    month_as_str: str = field(init=False)

    def __post_init__(self):
        self.day = int(self.day)
        self.year = int(self.year)

        try:
            self.month = int(self.month)
        except ValueError:
            self.month = MONTHS.index(str(self.month).lower()) - 1

        if not 1 <= self.month <= 12:
            raise InvalidMonthError(f"{self.month} is not a valid month [1-12]")

        self.month_as_str = MONTHS[self.month - 1]

        day_of_week = datetime.datetime(self.year, self.month, self.day).strftime('%A').upper()
        self.day_of_week_as_str = ACCENT_DAYS[ENGLISH_DAYS.index(day_of_week)].capitalize()

    @property
    def id(self) -> int:
        """Returns the id of a menu, formed by year, month and day."""
        return int(f'{self.year:04d}{self.month:02d}{self.day:02d}')

    @property
    def date(self) -> datetime.date:
        """Returns the date of the menu as an instance of datetiem.date"""
        return datetime.date(self.year, self.month, self.day)

    @staticmethod
    def generate_id(month_day: int, month: int, year: int) -> int:
        """Genera la id de un menú.

        Args:
            month_day (int): day of the month.
            month (int): month.
            year (int): year.
        """
        return int(f'{year:04d}{month:02d}{month_day:02d}')

    def __lt__(self, other):
        return self.id < other.id

    def __str__(self, arg='all', html=False, minimal=False):

        if minimal is True and arg == 'all':
            logger = logging.getLogger(__name__)
            logger.warning('Too much information (minimal=True, arg=\'all\')')

        output = ''
        if html is True:
            output += '<b>'
        if minimal is False:
            output += "{} de {} de {} ({}):".format(
                self.day, self.month_as_str, self.year, self.day_of_week_as_str)
        if html is True:
            output += '</b>'

        if minimal is False:
            output += '\n'

        if arg in ('launch', 'all'):
            if self.launch1 is not None:
                output += f'Comida: {self.launch1}'
                if self.launch2 is not None:
                    output += f' y {self.launch2}'

        if arg == 'all':
            output += '\n'

        if arg in ('dinner', 'all'):
            if self.dinner1 is not None:
                output += f'Cena: {self.dinner1}'
                if self.dinner2 is not None:
                    output += f' y {self.dinner2}'

        return output


class MenusManager:
    """Manages a list of menus."""

    def __init__(self, url=None):
        self.logger = logging.getLogger(__name__)
        self.logger.debug('Starting menus manager')

        self.url = url or "https://www.residenciasantiago.es/menus-1/"
        self.updated = False
        self.list = []
        self.opcodes = []
        self.downloader = Downloader()
        self.database_manager = MenusDatabaseManager()

        # Patterns:
        # 1. Detects "DÍA: 28 DE JUNIO DE 2018 (JUEVES)".
        # 2. Detects "28/06/2018".
        # 3. Detects "27. junio 2018" (unused).
        # 4. Detects when "1ER PLATO" is splitted from the dinner itself (or the 2nd)
        # 5. Detects when there are no dinner plates, and takes until dessert.

        self.pattern1 = re.compile(r'DÍA:\s\d{2}\sDE\s[a-zA-Z]{4,10}\sDE\s\d{4}\s\(\w{5,9}\)',
                                   re.IGNORECASE)
        self.pattern2 = re.compile(r'\d{2}/\d{2}/\d{4}', re.IGNORECASE)
        # self.pattern3 = re.compile(r'\d{2}\.\s[a-zA-Z]{4,10}\s\d{4}', re.IGNORECASE)
        self.pattern4 = re.compile(r'((1ER|2º)\sPLATO:\${3}[\w\s]*)', re.IGNORECASE)
        self.pattern5 = re.compile(r'(?<=CENA:\${3})(?!(1ER))[\w\s.:,;$]+(?=\${3}POSTRE)',
                                   re.IGNORECASE)

        self.opcodes_lock = threading.Lock()
        self.sqlite_lock = threading.Lock()
        self.links_to_save = []

        if self.load():
            self.logger.debug('Menus manager loaded')
        else:
            self.logger.critical('Error loading menus')

    def __contains__(self, item):
        if isinstance(item, int):
            return item in (x.id for x in self)
        raise TypeError('ID must be an integer')

    def __iter__(self):
        return iter(self.list)

    def load_from_database(self):
        """Loads the menus from the database."""

        self.logger.debug('Loading menus from database')
        menus = self.database_manager.extract_menus_data()
        for row in menus:
            _, origin, day, month, year, _, launch1, launch2, dinner1, dinner2 = row
            menu = Menu(
                day=day, month=month, year=year,
                launch1=launch1, launch2=launch2, dinner1=dinner1, dinner2=dinner2, origin=origin
            )
            self.list.append(menu)

    def save_to_database(self) -> int:
        """Saves the menus to the database.

        Returns:
            int: number of menus saved to the database.

        """
        self.logger.debug('Saving menus to database')
        i = 0
        for menu in self:
            out = self.database_manager.save_menu(menu)
            if out:
                i += 1
        self.database_manager.save_changes()

        self.logger.debug('Saved %s menus to database', i)
        return i

    def sort(self, **kwargs):
        """Sorts the menu list."""
        self.list.sort(**kwargs)

    def update(self, day, month, year, **kwargs):
        """Updates some attributes of a specified menu."""
        possible_days = [x for x in self.list if x.day == day]

        for menu in possible_days:
            if menu.month == month and menu.year == year:
                index = self.list.index(menu)

                if "launch1" in kwargs:
                    menu.launch1 = kwargs.pop("launch1")
                if "launch2" in kwargs:
                    menu.launch2 = kwargs.pop("launch2")
                if "dinner1" in kwargs:
                    menu.dinner1 = kwargs.pop("dinner1")
                if "dinner2" in kwargs:
                    menu.dinner2 = kwargs.pop("dinner2")
                self.list[index] = menu
                break
        else:
            menu = Menu(day, month, year)

            if "launch1" in kwargs:
                menu.launch1 = kwargs.pop("launch1")
            if "launch2" in kwargs:
                menu.launch2 = kwargs.pop("launch2")
            if "dinner1" in kwargs:
                menu.dinner1 = kwargs.pop("dinner1")
            if "dinner2" in kwargs:
                menu.dinner2 = kwargs.pop("dinner2")
            self.list.append(menu)

    def load(self):
        """Loads all the menus required."""
        self.load_from_database()

        three_days_ahead = datetime.datetime.today() + datetime.timedelta(days=3)
        day, month, year = three_days_ahead.day, three_days_ahead.month, three_days_ahead.year

        current_id = Menu.generate_id(day, month, year)

        if current_id in self:
            return True

        if datetime.datetime.today() - self.database_manager.get_update() <= datetime.timedelta(
                seconds=60 * 20):
            self.logger.debug('Web not processed - less than 20 minutes since last update')
            return False

        self.logger.debug('Processing web - more than 20 minutes since last update')
        self.updated = True
        self.download_and_process_web()
        self.save_to_database()
        self.database_manager.set_update()

        return True

    @staticmethod
    def load_csv(csvpath):
        """Gets the menus by a csv file splitted by ;. Example: 31;12;18;launch1;launch2..."""
        self = object.__new__(MenusManager)
        self.__init__(None)

        self.logger.debug('Loading from csv')

        with open(csvpath, encoding='utf-8') as file_handler:
            contenido = file_handler.read().splitlines()

        contenido = [x.split(';') for x in contenido]
        contenido = [[elemento.strip() for elemento in fila] for fila in contenido]
        cont1 = ['a', 'al', 'la', 'ante', 'bajo', 'con', 'contra', 'de', 'del', 'desde', 'durante',
                 'en', 'hacia',
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
                for i, _ in enumerate(cont1):
                    elemento = elemento.replace(titled[i], cont1[i])
                try:
                    elemento = int(elemento)
                except ValueError:
                    pass
                copia_fila.append(elemento)
            copia.append(copia_fila)

        contenido = copia

        for fila in contenido:
            self.list.append(Menu(fila[0], fila[1], fila[2], launch1=fila[3], launch2=fila[4],
                                  dinner1=fila[5], dinner2=fila[6], origin='manual'))

        guardado = self.save_to_database()
        self.logger.debug('Saved %s menus in the data base', guardado)
        return guardado

    def download_and_process_web(self):
        """Downloads and processes web page."""

        self.logger.debug('Downloading and processing %r', self.url)
        opcodes = self.generate_opcodes(self.url)
        if opcodes == -1:
            return -1
        lista = self.process_opcodes()

        cont1 = ['a', 'al', 'ante', 'bajo', 'con', 'contra', 'de', 'del',
                 'desde', 'durante', 'en', 'hacia', 'hasta', 'mediante', 'o',
                 'para', 'por', 'según', 'sin', 'sobre', 'tras', 'y']

        titled = [' ' + x.title() + ' ' for x in cont1]

        for element in lista:
            ano = int(element['year'])
            mes = int(element['mes'])
            dia = int(element['dia'])
            code = element['code']
            value = element['value']

            for k in titled:
                if k in value:
                    value = value.replace(k, k.lower())

            value = value.replace(" Y ", " y ")
            value = value.replace(" A ", " a ")
            value = value.replace(" Al ", " al ")
            value = value.replace(" De ", " de ")
            value = value.replace(" La ", " la ")
            value = value.replace(" Con ", " con ")

            if code == "L1":
                self.update(dia, mes, ano, launch1=value)
            elif code == "L2":
                self.update(dia, mes, ano, launch2=value)
            elif code == "D1":
                self.update(dia, mes, ano, dinner1=value)
            elif code == "D2":
                self.update(dia, mes, ano, dinner2=value)

        return self

    def generate_opcodes(self, url):
        """Downloads url and creates opcodes."""

        self.logger.debug('Generating opcodes')

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

        return 0

    def append_to_opcodes(self, anything):
        with self.opcodes_lock:
            self.opcodes.append(anything)

    def procesar_url_menus(self, url):
        self.logger.debug('Processing web %r', url)

        try:
            html = self.downloader.get(url)
        except DownloaderError:
            self.logger.error('Skipped: %r', url)
            return

        with self.sqlite_lock:
            self.links_to_save.append(url)
        sopa = Soup(html.text, "html.parser")

        resultado = sopa.find('article', {'class': 'j-blog'})
        textos = resultado.text.split('\n')

        for i, _ in enumerate(textos):
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
                if not elem:
                    break

            if not elem:
                continue

            if self.pattern2.match(elem):
                elem = extend_date(elem)

            if elem.count("DÍA:"):
                for match in matches:
                    if elem in match:
                        elem = match
                        break
                dia_mes = elem[5:7]
                for i, _ in enumerate(MONTHS):
                    if elem.lower().count(MONTHS[i]):
                        index_meses = i
                        break
                else:
                    continue
                mes = MONTHS[index_meses]
                ano = elem[15 + len(mes):19 + len(mes)]
                dia_mes, ano = [int(x) for x in [dia_mes, ano]]

                for i, _ in enumerate(DAYS):
                    if elem.lower().count(DAYS[i]) != 0:
                        index_dias = i
                        break
                else:
                    for i, _ in enumerate(ACCENT_DAYS):
                        if elem.lower().count(ACCENT_DAYS[i]) != 0:
                            index_dias = i
                            break
                    else:
                        raise InvalidDayError(f'Error en el día: {elem}')
                dia_semana = ACCENT_DAYS[index_dias].title()

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
        """Transforma una list del tipo [OPCODE] [VALOR] en una lista con la
         información de cada opcode extraída en
        forma de diccionario."""

        self.logger.debug('Processing opcodes')
        salida = []
        for line in self.opcodes:
            output = {}
            opcode = line[:10]
            value = line[11:].title()

            ano = int(opcode[:4])
            mes = int(opcode[4:6])
            dia = int(opcode[6:8])
            code = opcode[8:10]

            if code == 'xx':
                value = value.capitalize()

            output['year'] = ano
            output['mes'] = mes
            output['dia'] = dia
            output['code'] = code
            output['value'] = value
            salida.append(output)

        return salida

    def week_to_str(self, today):
        output = ''
        counter = 0
        level = today - datetime.timedelta(days=7)
        for menu in self:
            if today >= menu.date >= level:
                counter += 1
                output += menu.__str__(html=True)
                output += '\n\n'
        if counter == 0:
            return False
        return output
