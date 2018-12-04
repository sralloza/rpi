# -*- coding: utf-8 -*-

from rpi.dns import RpiDns


class GestorConfig(dict):
    def __init__(self):
        super(GestorConfig, self).__init__()
        self.path = RpiDns.get('textdb.config')
        self.cargar()

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
