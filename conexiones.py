# -*- coding: utf-8 -*-

import datetime
import os
import platform
import smtplib
import sqlite3
from _socket import gaierror
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from threading import Lock, Thread

import gspread
import httplib2
from gspread import WorksheetNotFound
from gspread.exceptions import APIError
from oauth2client.service_account import ServiceAccountCredentials as Sac
from requests.exceptions import ConnectionError

from .dns import RpiDns
from .downloader import Downloader
from .exceptions import NeccessaryArgumentError, UnrecognisedUsernameError, ApiError, DownloaderError, \
    AuxiliarFileError
from .gestor_claves import GestorClaves
from .gestor_usuarios import GestorServicios, rpi_gu
from .rpi_logging import Logger

debug_lock = Lock()
logger = Logger.get(__file__, __name__)


class Conexiones:
    """Clase para gestionar todas las conexiones salientes."""
    gu = rpi_gu
    DISABLE = platform.system() == 'Windows'

    def __init__(self):
        self.lock = Lock()
        self.errores = []
        self._downloader = Downloader()

    def append_error(self, something):
        with self.lock:
            self.errores.append(something)

    @staticmethod
    def forzar_notificacion(title, message, destino=None):
        """Manda una notifición a uno o varios usuarios, independientemente del servicio.
        :param str title: título de la notificación.
        :param str message: mensaje de la notificación.
        :param destino: usuarios(s) a notificar.
        :type destino: iterable / str.
        :return:
        """
        return Conexiones.notificacion(title, message, destino, _forzar_notificacion=True)

    @staticmethod
    def notificacion(title, message, destino=None, file=None, _forzar_notificacion=False):
        """Manda una notificación a un dispositivo móvil preparado (usando IFTTT).

        :param str title: título de la notificación.
        :param str message: mensaje de la notificación.
        :param destino: destino(s) a los que les debe llegar.
        :type destino: str/list/tuple.
        :param str file: ruta del archivo del que se llama para comprobar el servicio que lo ejecuta. Se debe pasar
            como parámetro ``__file__``
        :param bool _forzar_notificacion: forzar el envío de la notificación, inhabilitando el valor de **file**.
        :return: False si algo ha ido mal, True si ha funcionado correctamente.
        :rtype: bool
        """

        self = object.__new__(Conexiones)
        self.__init__()

        if file is None and _forzar_notificacion is False:
            raise NeccessaryArgumentError(f"Debe especificar el parámetro 'file' para comprobar los permisos.")

        if destino == 'broadcast' and file is None:
            raise NeccessaryArgumentError("No se puede usar broadcast si no se especifica el parámetro 'file'.")

        # Servicio
        servicio = GestorServicios.get(file) if file is not None else GestorServicios.LOG

        # Preparación del mapa de destinos
        destinos = {x: False for x in Conexiones.gu}
        if destino is None:
            destino = 'all'

        if isinstance(destino, str):
            # Si el usuario destino es 'all', se manda a todos los usuarios
            if destino == 'all':
                for usuario in Conexiones.gu:
                    destinos[usuario] = True

            # Si el usuario destino es 'broadcast', se manda a todos los usuarios afiliados al servicio.
            elif destino == 'broadcast':
                for usuario in Conexiones.gu:
                    if servicio in usuario.servicios:
                        destinos[usuario] = True

                # Si el usuario destino no está registrado, lanza excepción
            elif destino not in Conexiones.gu.usernames:
                raise UnrecognisedUsernameError('Usuario no afiliado: ' + destino)
            else:
                destinos[Conexiones.gu.get_by_username(destino)] = True

        else:
            if 'all' in destino:
                for afiliado in Conexiones.gu:
                    destinos[afiliado] = True
            else:
                try:
                    for persona in destino:
                        if persona not in Conexiones.gu.usernames:
                            raise UnrecognisedUsernameError('Usuario no afiliado: ' + str(destino))
                        else:
                            destinos[Conexiones.gu.get_by_username(persona)] = True
                except TypeError:
                    logger.critical('"destino" debe ser str o iterable, no ' + type(destino).__name__)
                    raise TypeError('"destino" debe ser str o iterable, no ' + type(destino).__name__)

        threads = []
        for usuario in Conexiones.gu:
            if destinos[usuario] is False:
                continue
            if servicio not in usuario.servicios and _forzar_notificacion is False:
                logger.warning(
                    f"El usuario '{usuario.username}' no está registrado en el servicio '{servicio.nombre}'")
                continue

            logger.debug('Iniciando hilo de conexión de ' + usuario.username)
            threads.append(
                Thread(name=usuario.username, target=self._notificar, args=(usuario, title, message), daemon=True))
            threads[-1].start()

        for thread in threads:
            thread.join()

        logger.debug('Hilos de conexión finalizados')

        report = {'value1': title, 'value2': message}

        if len(self.errores) > 0:
            report['destino'] = self.errores
            report['code'] = 404
            Conexiones.log('Notificacion', str(report))
            logger.error('Errores en notificación: ' + str(report))
            return False
        else:
            return True

    def _notificar(self, usuario, title, message):
        """Método auxiliar de notificación. Envía los datos report a la web de usuario.

        :param Usuario usuario: usuario al que enviar la notificación.
        """

        try:
            if usuario.esta_activo is False:
                logger.warning('[Usuario desactivado] ' + usuario.username)
                return False

            if Conexiones.DISABLE is True:
                logger.warning('[Notificaciones deshabilitadas] ' + usuario.username)
                return False
            else:
                usuario.launcher.fire(title, message)
                logger.debug('Enviada notificación a ' + usuario.username)
                return True
        except DownloaderError:
            self.append_error(usuario)

    @staticmethod
    def enviar_email(destiny, subject, mensaje, files=None, is_file=False, force_file_name=None, origin='Rpi'):
        """Función para enviar un email.

        :param destiny: correo electrónico de destino.
        :type destiny: str/list/tuple
        :param str subject: asunto del correo electrónico.
        :param str mensaje: mensaje HTML del correo electrónico. Los saltos de línea se cambian automáticamente por
            los saltos de línea de html, la etiqueta ``<br>``.
        :param files: lista de archivos o archivo a enviar por correo.
        :type files: str/list/tuple
        :param bool is_file: indica si **files** es un archivo o es un objeto generado con ´´open()´´.
        :param str force_file_name: indica el nombre del archivo que se usará para enviar el correo.
        :param str origin: indica el alias de la dirección de correo electrónico que hace el envío.

        """
        intentos = 10
        if isinstance(destiny, list) or isinstance(destiny, tuple):
            destiny = ', '.join(destiny)

        if files is not None and is_file is True and force_file_name is None:
            raise NeccessaryArgumentError(
                "Si 'is_file' es True, se debe especificar el nombre del archivo ('force_file_name')")

        password = GestorClaves.get('mail_password')
        username = GestorClaves.get('mail_username')

        while True:
            try:

                msg = MIMEMultipart()
                msg['From'] = f"{origin} <{username}>"
                msg['To'] = destiny
                msg['Subject'] = subject

                body = mensaje.replace('\n', '<br>')
                msg.attach(MIMEText(body, 'html'))

                if isinstance(files, tuple) or isinstance(files, list):
                    for file in files:
                        part = MIMEBase('application', "octet-stream")
                        if is_file is False:
                            part.set_payload(open(file, "rb").read())
                        else:
                            part.set_payload(file)
                        encoders.encode_base64(part)

                        realfilename = os.path.basename(file) if force_file_name is None else force_file_name
                        part.add_header('Content-Disposition', 'attachment', filename=realfilename)

                        msg.attach(part)
                else:
                    if files is not None:
                        part = MIMEBase('application', "octet-stream")
                        if is_file is False:
                            part.set_payload(open(files, "rb").read())
                        else:
                            part.set_payload(files)
                        encoders.encode_base64(part)

                        realfilename = os.path.basename(files) if force_file_name is None else force_file_name
                        part.add_header('Content-Disposition', 'attachment', filename=realfilename)

                        msg.attach(part)
                server = smtplib.SMTP("smtp.gmail.com", 587)
                server.starttls()
                server.login(username, password)
                server.sendmail(username, msg['To'], msg.as_string())
                server.quit()
                break
            except (ConnectionError, gaierror, smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected):
                intentos -= 1
                logger.warning('Error al enviar mail, reintentando.')
            except smtplib.SMTPSenderRefused as e:
                logger.error('Error fatal al enviar mail: ' + str(e))
                return False
            if intentos == 0:
                return False
        return True

    @staticmethod
    def log(servicio, info):
        """Método para loguear algo. Se guarda en una base de datos sqlite local y en google sheets.

        :param str servicio: servicio que quiere hacer el log.
        :param str info: información a loguear.
        """

        logger.debug(f'Guardar log - [{servicio}] {info}')
        intentos = 10
        datos = (
            datetime.datetime.today().strftime('%Y-%m-%d'),
            datetime.datetime.today().strftime('%H:%M:%S'),
            servicio, info)

        logger.debug('Iniciando log.spreadsheets')
        while True:
            try:
                # Cosas raras que hay que hacer para usar Google Sheets
                scope = ['https://spreadsheets.google.com/feeds',
                         'https://www.googleapis.com/auth/drive']
                if platform.system() == 'Linux':
                    credentials = Sac.from_json_keyfile_name(RpiDns.get('credenciales.googlesheets'), scope)
                else:
                    credentials = Sac.from_json_keyfile_name(
                        'D:/.database/json/Spreadsheets Python-0944c9fde924.json', scope)
                gcc = gspread.authorize(credentials)

                # Abrimos Spreadsheet llamada 'pylog', en la hoja 'logs'
                archivo = gcc.open('pylog')
                wks = archivo.worksheet('logs')

                # Insertamos los datos en una nueva línea
                wks.append_row(datos)
                spreadsheets = True
                break

            except (httplib2.ServerNotFoundError, ConnectionError, TimeoutError):
                intentos -= 1
                error_code = 404
                logger.warning('Error en log.spreadsheets, reintentando')

            if intentos == 0:
                logger.error('Error fatal en log.spreadsheets (' + str(error_code) + ')')
                spreadsheets = False
                break

        logger.debug('Iniciando log.sqlite')
        intentos = 10
        while True:
            try:
                # Conectamos con la base de datos
                if platform.system() == 'Linux':
                    con = sqlite3.connect(RpiDns.get('sqlite.log'))
                else:
                    con = sqlite3.connect('D:/.database/sql/log.sqlite')
                cur = con.cursor()

                # Si no existe la tabla, la creamos
                cur.execute('''CREATE TABLE IF NOT EXISTS 'log' (
                    'id' INTEGER PRIMARY KEY AUTOINCREMENT,
                    'fecha' INTEGER NOT NULL,
                    'hora' VARCHAR NOT NULL,
                    'servicio' VARCHAR NOT NULL,
                    'info' VARCHAR NOT NULL)''')

                # Insertamos los datos, guardamos y cerramos la conexión
                cur.execute(
                    "INSERT INTO 'log' VALUES (NULL, ?, ?, ?, ?)", datos)
                con.commit()
                con.close()
                sqlite = True
                break

            except TypeError:
                logger.warning('Error en log.sqlite, reintentando')
                intentos -= 1

            if intentos == 0:
                logger.error('Error fatal en log.sqlite')
                sqlite = False
                break

        return sqlite and spreadsheets

    @staticmethod
    def to_spreadsheets(sheetname, data):
        """Guarda la información en tuplas data en la hoja de cálculo sheetname.
        :param str sheetname: nombre de la hoja donde se guardará la información.
        :param tuple data: información a guardar.

        """

        logger.debug(f'Google Spreadsheets - [{sheetname}] {data}')
        intentos = 10

        logger.debug('Iniciando log.spreadsheets')
        while True:
            try:
                # Cosas raras que hay que hacer para usar Google Sheets
                scope = ['https://spreadsheets.google.com/feeds',
                         'https://www.googleapis.com/auth/drive']
                if platform.system() == 'Linux':
                    credentials = Sac.from_json_keyfile_name(RpiDns.get('credenciales.googlesheets'), scope)
                else:
                    credentials = Sac.from_json_keyfile_name(
                        'D:/.database/json/Spreadsheets Python-0944c9fde924.json', scope)
                gcc = gspread.authorize(credentials)

                # Abrimos Spreadsheet llamada 'pylog', en la hoja 'logs'
                archivo = gcc.open('pylog')

                try:
                    wks = archivo.worksheet(sheetname)
                except WorksheetNotFound:
                    logger.critical('Hoja de cálculo no encontrada: ' + sheetname)
                    return

                # Insertamos los datos en una nueva línea
                try:
                    wks.append_row(data)
                except APIError as e:
                    error = str(e)
                    error_evaluado = eval(error)
                    error_code = error_evaluado['error']['code']
                    error_message = error_evaluado['error']['message']
                    logger.critical(f"APIERROR: [{error_code}] '{error_message}'")
                    raise ApiError(f"[{error_code}] '{error_message}'")
                break

            except httplib2.ServerNotFoundError:
                logger.warning('Error buscando el servidor, reintentando')
                intentos -= 1
                error_code = 404

            except OSError:
                logger.warning('Error del sistema, reintentando')
                intentos -= 1
                error_code = 418

            if intentos == 0:
                logger.error('Error fatal guardando información en spreadsheets (' + str(error_code) + ')')
                break


if __name__ == '__main__':
    raise AuxiliarFileError('Archivo auxiliar, no ejecutable.')
