# -*- coding: utf-8 -*-

"""Domain Name System of the Raspberry Pi"""

import platform
import sqlite3
from difflib import SequenceMatcher

from rpi.exceptions import UnknownError, DnsError, PlatformError


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

    def __len__(self):
        return len(self.alias())

    def close(self):
        self.con.commit()
        self.con.close()
        del self.con
        del self.cur

    def _del_alias(self, alias):

        try:
            self.get(alias)
        except DnsError:
            raise DnsError(f'Alias not found ({alias!r})')

        self.cur.execute('DELETE FROM dns WHERE alias=?', (alias,))
        self.close()

    @staticmethod
    def _get_number_subalias(alias):
        return len(alias.split('.'))

    @staticmethod
    def len():
        return len(RpiDns.alias())

    @staticmethod
    def extend_alias(alias):
        splitted = alias.split('.')
        if len(splitted) < 2:
            raise DnsError(f'Not enough subalias ({alias})')
        if len(splitted) == 2:
            alias = platform.system() + '.' + alias
        if len(splitted) == 3:
            if splitted[0].lower() not in ('linux', 'windows'):
                raise PlatformError(f'Invalid platform: {splitted[0].lower()}')

        alias = alias.lower()

        return alias

    @staticmethod
    def alias():
        """Returns the alias of the addresses stored"""

        self = object.__new__(RpiDns)
        self.__init__()
        self.cur.execute("SELECT alias FROM dns")
        data = tuple((x[0] for x in self.cur.fetchall()))
        self.close()

        return data

    @staticmethod
    def new_alias(alias, address):
        self = object.__new__(RpiDns)
        self.__init__()

        alias = RpiDns.extend_alias(alias)

        try:
            self.cur.execute("INSERT INTO dns VALUES(NULL, ?, ?)", (alias, address), )
        except sqlite3.IntegrityError:
            raise DnsError(f'Alias {alias!r} already exists')
        self.close()

    @staticmethod
    def del_alias(alias,error=True):
        number_of_subalias = RpiDns._get_number_subalias(alias)
        if number_of_subalias == 3:
            return RpiDns()._del_alias(alias)
        elif number_of_subalias == 2:
            try:
                RpiDns()._del_alias('windows.' + alias)
            except DnsError:
                if not error:
                    raise

            try:
                RpiDns()._del_alias('linux.' + alias)
            except DnsError:
                if not error:
                    raise
            return
        else:
            RpiDns.extend_alias(alias)

    @staticmethod
    def new_dual_alias(alias, windows_address, linux_address):
        """Creates a new alias, both for linux and windows."""

        splitted = alias.split('.')
        if len(splitted) != 2:
            raise DnsError(f'For dual alias, 2 subalias must be given ({alias!r})')

        alias_windows = 'windows.' + alias
        alias_linux = 'linux.' + alias

        RpiDns.new_alias(alias_windows, windows_address)
        RpiDns.new_alias(alias_linux, linux_address)

    @staticmethod
    def _similar(this, other):
        """Returns the similarity between this and other in the interval [0,1]."""
        return SequenceMatcher(None, this, other).ratio()

    def _get(self, alias):
        """Returns the address whose alias is more close to alias."""

        if len(self) == 0:
            raise DnsError('Emtpy dns')

        ratios = {x: self._similar(alias.lower(), x.lower()) for x in self.alias()}
        max_ratio = max(ratios.values())

        if max_ratio < 0.9:
            raise DnsError(f'Not enough similarity ({max_ratio * 100:.2f} %)')

        for key, value in ratios.items():
            if max_ratio == value:
                self.cur.execute("SELECT address FROM dns WHERE alias=?", (key,))
                data = self.cur.fetchone()
                return data[0]

        raise UnknownError('FATAL ERROR')

    @staticmethod
    def get(alias):
        """Returns the address given its alias."""

        self = object.__new__(RpiDns)
        self.__init__()

        alias = RpiDns.extend_alias(alias)

        if alias not in self.alias():
            return self._get(alias)

        self.cur.execute("SELECT address FROM dns WHERE alias=?", (alias,))
        data = self.cur.fetchone()
        self.close()
        return data[0]
