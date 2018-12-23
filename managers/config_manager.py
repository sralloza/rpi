# -*- coding: utf-8 -*-

from rpi.dns import RpiDns
from rpi.exceptions import ConfigNotFoundError, EmptyConfigError


class GestorConfig(object):
    def __init__(self):
        super(GestorConfig, self).__init__()
        self.path = RpiDns.get('textdb.config')
        self.data = {}
        self.cargar()

    def __setitem__(self, key, value):
        self.data[key] = value

    def __getitem__(self, item):
        return self.data[item]

    def __delitem__(self, key):
        del self.data[key]

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def __contains__(self, item):
        return item in self.data

    def cargar(self):
        try:
            with open(self.path, 'rt', encoding='utf-8') as fh:
                datos = fh.read()
        except FileNotFoundError:
            raise FileNotFoundError(f'No existe el archivo de configuración ({self.path!r})')

        for linea in datos.splitlines():
            clave, *valor = linea.split('=')

            clave = clave.strip()
            valor = '='.join(valor).strip()

            self[clave] = valor

    def guardar(self, force=False):
        if len(self) == 0 and force is False:
            raise EmptyConfigError('No hay información que guardar')
        with open(self.path, 'wt', encoding='utf-8') as fh:
            for key, value in self.data.items():
                fh.write(f"{key}={value}\n")

    @staticmethod
    def get(configuracion):
        self = GestorConfig.__new__(GestorConfig)
        self.__init__()

        if configuracion not in self:
            raise ConfigNotFoundError(f'Configuración no encontrada: {configuracion}')

        valor = self[configuracion]

        return valor

    @staticmethod
    def set(configuracion, valor):
        self = GestorConfig.__new__(GestorConfig)
        self.__init__()

        self[configuracion] = valor

        self.guardar()

    @staticmethod
    def delete(configuracion):
        self = GestorConfig.__new__(GestorConfig)
        self.__init__()

        del self[configuracion]
        self.guardar(force=True)

    @staticmethod
    def listar():
        self = GestorConfig.__new__(GestorConfig)
        self.__init__()

        return tuple(self.data.keys())
