# -*- coding: utf-8 -*-

"""Domain Name System of the Raspberry Pi"""

import platform
import sqlite3
import warnings
from difflib import SequenceMatcher

from rpi.exceptions import TooLowAccuracy, UnknownError, DnsError


# WARNING: THIS FILE DOES NOT USE LOG DUE TO IMPORT ERRORS.

class RpiDns:
    """Dns for the entire system."""
    if platform.system() == 'Linux':
        PATH = '/home/pi/.database/rpi_dns.sqlite'
    else:
        PATH = 'D:/.database/rpi_dns.sqlite'

    def __init__(self):
        self.con = sqlite3.connect(self.PATH)
        self.cur = self.con.cursor()
        self.cur.execute("""CREATE TABLE IF NOT EXISTS "dns" (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alias VARCHAR UNIQUE NOT NULL,
                    address VARCHAR UNIQUE NOT NULL)""")
        self._check()

    def _check(self):
        """For every alias checks that exists a windows version and a linux version."""

        self.cur.execute("SELECT alias FROM dns")
        data = tuple((x[0] for x in self.cur.fetchall()))
        windows = tuple((x for x in data if 'windows' in x))
        linux = tuple((x for x in data if 'linux' in x))

        windows = set((x.replace('windows.', '') for x in windows))
        linux = set((x.replace('linux.', '') for x in linux))

        win_dif = windows.difference(linux)
        lin_dif = linux.difference(windows)

        difs = win_dif.union(lin_dif)

        check = windows == linux

        if check is False:
            raise DnsError(f'There is a platform difference: {difs!r}')

    @staticmethod
    def alias():
        """Returns the alias of the addresses stored"""

        self = object.__new__(RpiDns)
        self.__init__()
        self.cur.execute("SELECT alias FROM dns")
        data = tuple((x[0] for x in self.cur.fetchall()))
        self.con.close()

        return data

    @staticmethod
    def new(alias, windows, linux):
        """Creates a new alias."""

        self = object.__new__(RpiDns)
        self.__init__()

        data_windows = ('windows.' + alias, windows)
        data_linux = ('linux.' + alias, linux)
        self.cur.execute("INSERT INTO dns VALUES(NULL, ?, ?)", data_windows)
        self.cur.execute("INSERT INTO dns VALUES(NULL, ?, ?)", data_linux)
        self.con.commit()
        self.con.close()

    @staticmethod
    def _similar(this, other):
        """Returns the similarity between this and other in the interval [0,1]."""
        return SequenceMatcher(None, this, other).ratio()

    def _get(self, alias):
        """Returns the address whose alias is more close to alias."""

        ratios = {x: self._similar(alias.lower(), x.lower()) for x in self.alias()}
        max_ratio = max(ratios.values())

        for key, value in ratios.items():
            if max_ratio == value:
                if max_ratio < 0.9:
                    warnings.warn(f"Got alias '{key}' from '{alias}' with less than 90% accuracy",
                                  TooLowAccuracy)
                self.cur.execute("SELECT address FROM dns WHERE alias=?", (key,))
                data = self.cur.fetchone()
                return data[0]

        raise UnknownError('FATAL ERROR')

    @staticmethod
    def get(alias):
        """Returns the address given its alias."""

        self = object.__new__(RpiDns)
        self.__init__()

        splitted = alias.split('.')

        if len(splitted) < 2:
            raise DnsError('Must give 2 or 3 tags.')
        if len(splitted) == 2:
            alias = platform.system().lower() + '.' + '.'.join(splitted)

        alias = alias.lower()

        if alias not in self.alias():
            return self._get(alias)

        self.cur.execute("SELECT address FROM dns WHERE alias=?", (alias,))
        data = self.cur.fetchone()
        self.con.close()
        return data[0]
