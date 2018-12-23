# -*- coding: utf-8 -*-

import datetime
import re
import sqlite3
import threading
import time
from sqlite3 import IntegrityError
from typing import List

from bs4 import BeautifulSoup as Soup

from rpi.connections import Connections
from rpi.dns import RpiDns
from rpi.downloader import Downloader
from rpi.exceptions import WrongCalledError, InvalidMonthError, InvalidDayError, DownloaderError
from rpi.managers.user_manager import UserManager
from rpi.launcher import BaseMinimalLauncher
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


def extender_fecha(anything):
    """Cambia una fecha o un conjunto de fechas del tipo 01/01/2018 a DIA: 01 de Enero de 2018 (Lunes)-"""
    output = []
    if isinstance(anything, str):
        try:
            p = _extender_fecha(anything)
            return p
        except ValueError:
            return anything
    else:
        iterable = anything

    for elemento in iterable:
        p = _extender_fecha(elemento)
        output.append(p)

    return output


def _extender_fecha(elemento):
    """Cambia una fecha del tipo 01/01/2018 a DIA: 01 de Enero de 2018 (Lunes)-"""
    numeros = elemento.split('/')
    dia, mes, ano = numeros
    dia = int(dia)
    mes = int(mes)
    ano = int(ano)
    f = datetime.datetime.strptime(f'{dia}-{mes}-{ano}', '%d-%m-%Y').strftime('%A').upper()
    f = TDIAS[EDIAS.index(f)]
    p = f'DÍA: {dia:02d} DE {MESES[mes - 1].upper()} DE {ano:04d} ({f.upper()})'
    return p


def fecha():
    """Devuelve el día, mes, y año actual. Está centralizado para poder editarlo en un futuro con rapidez."""
    p = GestorMenus.hoy()
    # return 5,6,18
    return p.day, p.month, p.year


class GestorBaseDatos:
    """Gestor de la base de datos de menús de la Residencia Santiago."""

    def __init__(self):
        logger.debug('inicializando gestor de base de datos')
        self.con = sqlite3.connect(RpiDns.get('sqlite.menus_resi'))
        self.cur = self.con.cursor()
        self.cur.execute("""CREATE TABLE IF NOT EXISTS "menus" (
                         id INTEGER PRIMARY KEY NOT NULL,
                         procedencia VARCHAR NOT NULL,
                         dia_mes INTEGER NOT NULL,
                         mes INTEGER NOT NULL,
                         ano INTEGER NOT NULL,
                         dia_semana VARCHAR,
                         comida1 VARCHAR,
                         comida2 VARCHAR,
                         cena1 VARCHAR,
                         cena2 VARCHAR)""")
        self.cur.execute("""CREATE TABLE IF NOT EXISTS "enlaces" (
                        'fecha_hora' VARCHAR NOT NULL,
                        'enlace' VARCHAR PRIMARY KEY NOT NULL                        
                        )""")
        self.con.commit()

    def __contains__(self, item):
        if isinstance(item, str) is False:
            raise TypeError(f"Sólo se aceptan links (str).")

        return item in self.extraer_enlaces()

    # ------   OPERACIONES CON ENLACES   ------
    def guardar_enlace(self, enlace):
        """Guarda un enlace web en la base de datos junto a la fecha y hora actual."""
        dia = datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        datos = (dia, enlace)

        try:
            self.cur.execute('INSERT INTO "enlaces" VALUES(?,?)', datos)
        except IntegrityError:
            return False
        return True

    def extraer_enlaces(self):
        self.cur.execute("SELECT enlace FROM enlaces")
        data = [x[0] for x in self.cur.fetchall()]
        return data

    # ------   OPERACIONES CON MENÚS   ------
    def guardar_menu(self, menu):
        """Guarda el menú de un día en la base de datos."""
        mes = MESES.index(menu.mes) + 1
        datos = (
            menu.id, menu.procedencia, menu.dia_mes, mes, menu.ano, menu.dia_semana, menu.comida_p1, menu.comida_p2,
            menu.cena_p1, menu.cena_p2)
        try:
            self.cur.execute('INSERT INTO "menus" VALUES(?,?,?,?,?,?,?,?,?,?)', datos)
        except IntegrityError:
            return False
        return True

    def guardar_cambios(self):
        """Guarda todos los cambios en la base de datos."""
        self.con.commit()

    def extraer_menus(self):
        """Extrae todos los datos de la base de datos."""
        self.cur.execute('SELECT * FROM "menus"')
        return self.cur.fetchall()

    def cerrar(self):
        """Guarda cambios y cierra la base de datos."""
        self.con.commit()
        self.con.close()
        del self.con
        del self.cur


class Menu:
    """Representa una comida de un día."""

    def __new__(cls, dia_mes, mes, ano, **kwargs):
        self = object.__new__(cls)

        self.mes_num = None
        self.dia_mes = dia_mes
        self.mes = mes
        self.ano = ano
        self.procedencia = kwargs.pop('procedencia', 'auto')

        if type(self.mes) == int:
            if not 1 <= mes <= 12:
                raise InvalidMonthError(f"{self.mes} is not a valid month [1-12]")
            self.mes_num = self.mes
            self.mes = MESES[self.mes - 1]
        else:
            self.mes_num = MESES.index(self.mes) + 1

        self.dia_semana = kwargs.pop("dia_semana", None)
        self.comida_p1 = kwargs.pop("comida_p1", None)
        self.comida_p2 = kwargs.pop("comida_p2", None)
        self.cena_p1 = kwargs.pop("cena_p1", None)
        self.cena_p2 = kwargs.pop("cena_p2", None)

        if self.dia_semana is None:
            foo = datetime.datetime(self.ano, self.mes_num, self.dia_mes).strftime('%A').upper()
            self.dia_semana = TDIAS[EDIAS.index(foo)].capitalize()

        return self

    @property
    def id(self):
        """Devuelve la id de un menú, formado por el año, el mes y el día del mes en orden."""
        return int(f'{self.ano:04d}{self.mes_num:02d}{self.dia_mes:02d}')

    @property
    def date(self):
        """Devuelve la fecha del menú en forma de instancia de datetime.date."""
        return datetime.date(self.ano, self.mes_num, self.dia_mes)

    @staticmethod
    def gen_id(dia_mes, mes, ano):
        """Genera la id de un menú."""
        return int(f'{ano:04d}{mes:02d}{dia_mes:02d}')

    def __str__(self, arg='default', html=False, minimal=False):

        if minimal is True and arg == 'default':
            logger.warning('Se envía demasiada información (minimal=True)')

        o = ''
        if html is True:
            o += '<b>'
        if minimal is False:
            o += "{} de {} de {} ({}):".format(
                self.dia_mes, self.mes, self.ano, self.dia_semana)
        if html is True:
            o += '</b>'

        if minimal is False:
            o += '\n'

        if arg == 'comida' or arg == 'default':
            if self.comida_p1 is not None:
                o += f'Comida: {self.comida_p1}'
                if self.comida_p2 is not None:
                    o += f' y {self.comida_p2}'

        if arg == 'default':
            o += '\n'

        if arg == 'cena' or arg == 'default':
            if self.cena_p1 is not None:
                o += f'Cena: {self.cena_p1}'
                if self.cena_p2 is not None:
                    o += f' y {self.cena_p2}'

        return o

    def __repr__(self):
        o = []
        if self.dia_mes:
            o.append(f"{repr(self.dia_mes)}")
        if self.mes:
            o.append(f"{repr(self.mes)}")
        if self.ano:
            o.append(f"{repr(self.ano)}")
        if self.dia_semana:
            o.append(f"dia_semana='{self.dia_semana}'")
        if self.comida_p1:
            o.append(f"comida_p1='{self.comida_p1}'")
        if self.comida_p2:
            o.append(f"comida_p2='{self.comida_p2}'")
        if self.cena_p1:
            o.append(f"cena_p1='{self.cena_p1}'")
        if self.cena_p2:
            o.append(f"cena_p2='{self.cena_p2}'")
        return "Menu(" + ", ".join(o) + ')'

    def __lt__(self, other):
        iself = None
        iother = None
        for i in range(len(MESES)):
            if MESES[i] == self.mes:
                iself = i

        for i in range(len(MESES)):
            if MESES[i] == other.mes:
                iother = i

        if iself is None:
            raise InvalidMonthError("{} is not a month".format(self.mes))
        if iother is None:
            raise InvalidMonthError("{} is not a month".format(other.month))

        if iself != iother:
            return iself < iother
        else:
            return self.dia_mes < other.dia_mes

    def __ge__(self, other):
        return self.date >= other.date


class GestorMenus(object):
    """Representa una lista de menús."""

    def __init__(self, **kwargs):
        logger.debug('inicializando gestor de menús')
        _autocalled = kwargs.pop('_autocalled', None)

        if _autocalled is None:
            raise WrongCalledError("Can't create GestorMenus object. "
                                   "Use classmethod load() instead")
        self.lista = []
        self._opcodes = []
        self._downloader = Downloader()
        self.gestor_base_datos = GestorBaseDatos()

        # Patrones:
        # 1. Detecta "DÍA: 28 DE JUNIO DE 2018 (JUEVES)".
        # 2. Detecta "28/06/2018".
        # 3. Detecta "27. junio 2018" (en desuso).
        # 4. Detecta cuando "1ER PLATO" se separa de la comida en sí (o el 2º).
        # 5. Detecta cuando en la cena no hay platos, y coge hasta el postre.

        self.pattern1 = re.compile(r'DÍA:\s\d{2}\sDE\s[a-zA-Z]{4,10}\sDE\s\d{4}\s\(\w{5,9}\)', re.IGNORECASE)
        self.pattern2 = re.compile(r'\d{2}/\d{2}/\d{4}', re.IGNORECASE)
        # self.pattern3 = re.compile(r'\d{2}\.\s[a-zA-Z]{4,10}\s\d{4}', re.IGNORECASE)
        self.pattern4 = re.compile(r'((1ER|2º)\sPLATO:\${3}[\w\s]*)', re.IGNORECASE)
        self.pattern5 = re.compile(r'(?<=CENA:\${3})(?!(1ER))[\w\s.:,;$]+(?=\${3}POSTRE)', re.IGNORECASE)

        self.opcodes_lock = threading.Lock()
        self.sqlite_lock = threading.Lock()
        self.enlaces_a_guardar = []

    def __contains__(self, item):
        lista = (x.id for x in self)
        if isinstance(item, int):
            return item in lista
        else:
            raise TypeError('Las IDs deben ser números enteros')

    def __iter__(self):
        return iter(self.lista)

    @staticmethod
    def hoy():
        """Devuelve la fecha actual en forma de instancia de datetime.date."""
        return datetime.date.today()

    def cargar_desde_base_datos(self):
        """Extrae todos los datos de la base de datos y los procesa."""

        logger.debug('Cargando desde base de datos')
        datos = self.gestor_base_datos.extraer_menus()
        for fila in datos:
            _, _, dia_mes, mes, ano, dia_semana, comida_p1, comida_p2, cena_p1, cena_p2 = fila
            menu = Menu(dia_mes, mes, ano, dia_semana=dia_semana, comida_p1=comida_p1, comida_p2=comida_p2,
                        cena_p1=cena_p1, cena_p2=cena_p2)
            self.lista.append(menu)

    def guardar_a_base_datos(self):
        """Guarda todos los menús en la base de datos."""
        logger.debug('Guardando a base de datos')
        i = 0
        for menu in self:
            out = self.gestor_base_datos.guardar_menu(menu)
            if out:
                i += 1
        self.gestor_base_datos.guardar_cambios()
        return i

    def sort(self, **kwargs):
        """Ordena la lista de menús por fecha."""
        self.lista.sort(**kwargs)

    def update(self, dia_mes, mes, ano, **kwargs):
        """Busca un menú y actualiza su información."""
        posibles_dias = [x for x in self.lista if x.dia_mes == dia_mes]

        for x in posibles_dias:
            if x.mes == mes and x.ano == ano:
                index = self.lista.index(x)

                if "dia_semana" in kwargs:
                    x.dia_semana = kwargs.pop("dia_semana")
                if "comida_p1" in kwargs:
                    x.comida_p1 = kwargs.pop("comida_p1")
                if "comida_p2" in kwargs:
                    x.comida_p2 = kwargs.pop("comida_p2")
                if "cena_p1" in kwargs:
                    x.cena_p1 = kwargs.pop("cena_p1")
                if "cena_p2" in kwargs:
                    x.cena_p2 = kwargs.pop("cena_p2")
                self.lista[index] = x
                break
        else:
            menu = Menu(dia_mes, mes, ano)

            if "dia_semana" in kwargs:
                menu.dia_semana = kwargs.pop("dia_semana")
            if "comida_p1" in kwargs:
                menu.comida_p1 = kwargs.pop("comida_p1")
            if "comida_p2" in kwargs:
                menu.comida_p2 = kwargs.pop("comida_p2")
            if "cena_p1" in kwargs:
                menu.cena_p1 = kwargs.pop("cena_p1")
            if "cena_p2" in kwargs:
                menu.cena_p2 = kwargs.pop("cena_p2")
            self.lista.append(menu)

    @classmethod
    def load(cls, url):
        """Crea y devuelve un objeto con todos los menús que encuentra."""

        self = object.__new__(cls)
        self.__init__(_autocalled=True)
        self.cargar_desde_base_datos()

        today_dia, today_mes, ano = fecha()

        id_hoy = Menu.gen_id(today_dia, today_mes, ano)

        if id_hoy in self:
            return self
        self.descargar_y_procesar_web(url)
        self.guardar_a_base_datos()

        return self

    @staticmethod
    def load_csv(csvpath):
        """Genera los menús a partid de un archivo csv separado por ; Ej: 31;12;2018;comida_p1;comida_p2...'"""
        self = object.__new__(GestorMenus)
        self.__init__(_autocalled=True)
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
            if 'dia_mes' in fila:
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
            self.lista.append(Menu(fila[0], fila[1], fila[2], comida_p1=fila[3], comida_p2=fila[4],
                                   cena_p1=fila[5], cena_p2=fila[6], procedencia='manual'))

        guardado = self.guardar_a_base_datos()
        logger.debug(f'Guardados {guardado} registros en la base de datos')
        return guardado

    def descargar_y_procesar_web(self, url):
        """Descarga y procesa la página web."""
        opcodes = self.opcodes(url)
        if opcodes == -1:
            return -1
        lista = self.procesar_opcodes()

        cont1 = ['a', 'al', 'ante', 'bajo', 'con', 'contra', 'de', 'del',
                 'desde', 'durante', 'en', 'hacia', 'hasta', 'mediante', 'o',
                 'para', 'por', 'según', 'sin', 'sobre', 'tras', 'y']

        titled = [' ' + x.title() + ' ' for x in cont1]

        for e in lista:
            ano = int(e['ano'])
            mes = MESES[e['mes'] - 1]
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

    def opcodes(self, url):
        """Descarga la web de la residencia y crea los opcodes."""

        try:
            html = self._downloader.get(url)
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
            if url in self.gestor_base_datos:
                continue
            hilo = threading.Thread(name=str(i), target=self.procesar_url_menus, args=(url,))
            hilo.start()
            hilos.append(hilo)
            i += 1

        for hilo in hilos:
            hilo.join()

        for enlace in self.enlaces_a_guardar:
            self.gestor_base_datos.guardar_enlace(enlace)

    def append_to_opcodes(self, anything):
        with self.opcodes_lock:
            self._opcodes.append(anything)

    def procesar_url_menus(self, url):

        try:
            html = self._downloader.get(url)
        except DownloaderError:
            logger.error('Skipped: ' + url)
            return

        with self.sqlite_lock:
            self.enlaces_a_guardar.append(url)
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
        matches = matches1 + extender_fecha(matches2)

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
                elem = extender_fecha(elem)

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

    def procesar_opcodes(self) -> List[dict]:
        """Transforma una lista del tipo [OPCODE] [VALOR] en una lista con la información de cada opcode extraída en
        forma de diccionario."""
        salida = []
        for line in self._opcodes:
            d = {}
            opcode = line[:10]
            value = line[11:].title()

            ano = int(opcode[:4])
            mes = int(opcode[4:6])
            dia = int(opcode[6:8])
            code = opcode[8:10]

            if code == 'xx':
                value = value.capitalize()

            d['ano'] = ano
            d['mes'] = mes
            d['dia'] = dia
            d['code'] = code
            d['value'] = value
            salida.append(d)

        return salida

    def to_txt(self):
        """Guarda los menús en un txt en el escritorio."""
        try:
            with open('D:/Sistema/Desktop/Menus.txt', 'w') as f:
                for menu in self:
                    f.write(str(menu))
                    f.write('\n\n')
        except FileNotFoundError:
            pass

    def semana_to_txt(self):
        """Guarda los menús de una semana en un txt."""
        with open('menus.txt', 'w', encoding='utf-8') as f:
            hoy = self.hoy()
            nivel = hoy - datetime.timedelta(days=7)
            for menu in self:
                if hoy >= menu.date >= nivel:
                    f.write(str(menu))
                    f.write('\n\n')

    def semana_to_string(self, hoy):
        """Genera un str con los menús de una semana."""
        p = ''
        contador = 0
        nivel = hoy - datetime.timedelta(days=7)
        for menu in self:
            if hoy >= menu.date >= nivel:
                contador += 1
                p += menu.__str__(html=True)
                p += '\n\n'
        if contador == 0:
            return False
        return p

    @staticmethod
    def notificar(mensaje, destinos_notificacion, mostrar='default'):
        titulo = 'Menús Resi'
        gu = UserManager.load()

        if isinstance(destinos_notificacion, str):
            if destinos_notificacion.lower() == 'all':
                destinos_notificacion = gu.usernames

        if isinstance(mensaje, Menu):
            mensaje_normal = mensaje.__str__(arg=mostrar)
            mensaje_minimal = mensaje.__str__(arg=mostrar, minimal=True)
        else:
            mensaje_minimal = mensaje
            mensaje_normal = mensaje

        if isinstance(destinos_notificacion, str):
            usuario = gu.get_by_username(destinos_notificacion).username
            if isinstance(usuario.launcher, BaseMinimalLauncher):
                Connections.notify(titulo, mensaje_minimal, destinations=usuario, file=__file__)
            else:
                Connections.notify(titulo, mensaje_normal, destinations=usuario, file=__file__)
        else:
            try:
                usuarios_normales = []
                usuarios_minimal = []
                for nombre in destinos_notificacion:
                    usuario = gu.get_by_username(nombre)
                    if isinstance(usuario.launcher, BaseMinimalLauncher):
                        usuarios_minimal.append(usuario.username)
                    else:
                        usuarios_normales.append(usuario.username)
                Connections.notify(titulo, mensaje_normal, destinations=usuarios_normales, file=__file__)
                Connections.notify(titulo, mensaje_minimal, destinations=usuarios_minimal, file=__file__)
            except TypeError:
                raise TypeError(
                    '"destinos_notificacion" debe ser str o iterable, no ' + type(destinos_notificacion).__name__)
