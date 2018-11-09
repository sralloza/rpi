# -*- coding: utf-8 -*-

import json

from .dns import RpiDns
from .exceptions import MissingKeyError, AuxiliarFileError
from .rpi_logging import Logger

logger = Logger.get(__file__, __name__)


class GestorClaves(object):
    """Gestiona las claves con las que trabajan los servicios."""

    def __init__(self):
        super().__init__()
        self.path = RpiDns.get('json.claves')
        with open(self.path) as f:
            self.dict = json.load(f)

    @staticmethod
    def keys():
        """Devuelve los servicios registrados.

        :rtype: tuple

        """
        self = object.__new__(GestorClaves)
        self.__init__()

        return tuple(self.dict.keys())

    def save(self):
        if self.dict is not None:
            with open(self.path, 'wt') as f:
                json.dump(self.dict, f, ensure_ascii=False, indent=4, sort_keys=True)

    @staticmethod
    def nueva(servicio, password):
        """Añade una nueva clave al servicio.

        :param str servicio: servicio a registrar.
        :param str password: contraseña a registrar.

        """

        self = object.__new__(GestorClaves)
        self.__init__()

        self.dict[servicio] = password
        self.save()

    @staticmethod
    def get(clave):
        """Devuelve una clave.

        :param str clave: palabra a buscar.
        :raises MissingKeyError: la clave no se encuentra en el registro.

        """

        self = object.__new__(GestorClaves)
        self.__init__()

        logger.debug(f'Buscando clave "{clave}".')

        if clave not in self.keys():
            logger.critical(f'Clave "{clave}" no encontrada.')
            raise MissingKeyError(f"La clave '{clave}' no se encuentra en el archivo de claves.")

        return self.dict[clave]


if __name__ == '__main__':
    raise AuxiliarFileError('Archivo auxiliar, no se puede ejecutar.')
