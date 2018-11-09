# -*- coding: utf-8 -*-

import platform
import sqlite3
import warnings
from difflib import SequenceMatcher

from .exceptions import TooLowAccuracy, UnknownError, AuxiliarFileError, DnsError


# ADVERTENCIA: ESTE ARCHIVO NO USA LOG DEBIDO A ERRORES DE IMPORTACIÓN.

class RpiDns(object):
    """Clase para obtener las direcciones de archivos en la Raspberry Pi."""
    if platform.system() == 'Linux':
        RUTA = '/home/pi/.database/rpi_dns.sqlite'
    else:
        RUTA = 'D:/.database/rpi_dns.sqlite'

    def __init__(self):
        self.con = sqlite3.connect(self.RUTA)
        self.cur = self.con.cursor()
        self.cur.execute("""CREATE TABLE IF NOT EXISTS "dns" (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alias VARCHAR UNIQUE NOT NULL,
                    address VARCHAR UNIQUE NOT NULL)""")
        self._check()

    def _check(self):
        self.cur.execute("SELECT alias FROM dns")
        datos = tuple((x[0] for x in self.cur.fetchall()))
        windows = tuple((x for x in datos if 'windows' in x))
        linux = tuple((x for x in datos if 'linux' in x))

        windows = set((x.replace('windows.', '') for x in windows))
        linux = set((x.replace('linux.', '') for x in linux))

        win_dif = windows.difference(linux)
        lin_dif = linux.difference(windows)

        difs = win_dif.union(lin_dif)

        check = windows == linux

        if check is False:
            raise DnsError('Hay diferencia de plataformas: ' + repr(difs))

    @staticmethod
    def alias():
        """Devuelve los alias de las direcciones almacenadas.

        :rtype: tuple

        """

        self = object.__new__(RpiDns)
        self.__init__()
        self.cur.execute("SELECT alias FROM dns")
        data = tuple((x[0] for x in self.cur.fetchall()))
        self.con.close()

        return data

    @staticmethod
    def insert(alias, address):
        """Inserta un nuevo alias en el registro.

        :param str alias: alias a registar.
        :param str address: dirección a registrar.

        """

        self = object.__new__(RpiDns)
        self.__init__()

        data = (alias, address)
        self.cur.execute("INSERT INTO dns VALUES(NULL, ?, ?)", data)
        self.con.commit()
        self.con.close()

    @staticmethod
    def _similar(a, b):
        """Devuelve la similitud entre a y b en el intervalo [0,1]."""
        return SequenceMatcher(None, a, b).ratio()

    def _get(self, alias):
        """Devuelve la dirección cuyo alias más se parecza a key.

        :raises: TooLowAccuracy: Hay una precisión menor que 90%.

        """

        ratios = {x: self._similar(alias.lower(), x.lower()) for x in self.alias()}
        max_ratio = max(ratios.values())

        for key, value in ratios.items():
            if max_ratio == value:
                if max_ratio < 0.9:
                    warnings.warn(f"Got alias '{key}' from '{alias}' with less than 90% accuracy", TooLowAccuracy)
                self.cur.execute("SELECT address FROM dns WHERE alias=?", (key,))
                data = self.cur.fetchone()
                return data[0]

        raise UnknownError('FATAL ERROR')

    @staticmethod
    def get(alias):
        """Devuelve la dirección real a partir de un alias.

        :param str alias: alias a buscar.

        :rtype: str
        :raises: TooLowAccuracy: Hay una precisión menor que 90%.
        """
        self = object.__new__(RpiDns)
        self.__init__()

        splitted = alias.split('.')
        if len(splitted) == 2:
            alias = platform.system().lower() + '.' + '.'.join(splitted)

        alias = alias.lower()

        if alias not in self.alias():
            return self._get(alias)
        else:
            self.cur.execute("SELECT address FROM dns WHERE alias=?", (alias,))
            data = self.cur.fetchone()
            self.con.close()
            return data[0]


if __name__ == '__main__':
    raise AuxiliarFileError("Can't open file because it's an auxiliar file.")
