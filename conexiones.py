# -*- coding: utf-8 -*-

import platform
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from threading import Lock, Thread

import gspread
from gspread import WorksheetNotFound
from gspread.exceptions import SpreadsheetNotFound
from oauth2client.service_account import ServiceAccountCredentials as Sac

from .dns import RpiDns
from .downloader import Downloader
from .exceptions import NeccessaryArgumentError, UnrecognisedUsernameError, DownloaderError, \
    SpreadsheetNotFoundError, SheetNotFoundError
from .gestores.gestor_claves import GestorClaves
from .gestores.gestor_usuarios import GestorServicios, GestorUsuarios
from .rpi_logging import Logger

debug_lock = Lock()
logger = Logger.get(__file__, __name__)


class Connections:
    """Manages every outgoing connection."""
    gu = GestorUsuarios.load()
    DISABLE = platform.system() == 'Windows'

    def __init__(self):
        self.lock = Lock()
        self.errores = []
        self._downloader = Downloader()

    def append_error(self, something):
        with self.lock:
            self.errores.append(something)

    @staticmethod
    def forzar_notificacion(title, message, destinations=None):
        return Connections.notificacion(title, message, destinations, force=True)

    @staticmethod
    def notificacion(title, message, destinations=None, file=None, force=False):
        # TODO: INSERT DOCSTRING
        # TODO: IMPROVE CODE
        # TODO: TRANSLATE INTO ENGLISH

        self = object.__new__(Connections)
        self.__init__()

        if file is None and force is False:
            raise NeccessaryArgumentError(f"Debe especificar el parámetro 'file' para comprobar los permisos.")

        if destinations == 'broadcast' and file is None:
            raise NeccessaryArgumentError("No se puede usar broadcast si no se especifica el parámetro 'file'.")

        # Servicio
        servicio = GestorServicios.get(file) if file is not None else GestorServicios.LOG

        # Preparación del mapa de destinos
        destinos = {x: False for x in Connections.gu}
        if destinations is None:
            destinations = 'all'

        if isinstance(destinations, str):
            # Si el usuario destinations es 'all', se manda a todos los usuarios
            if destinations == 'all':
                for usuario in Connections.gu:
                    destinos[usuario] = True

            # Si el usuario destinations es 'broadcast', se manda a todos los usuarios afiliados al servicio.
            elif destinations == 'broadcast':
                for usuario in Connections.gu:
                    if servicio in usuario.servicios:
                        destinos[usuario] = True

                # Si el usuario destinations no está registrado, lanza excepción
            elif destinations not in Connections.gu.usernames:
                raise UnrecognisedUsernameError('Usuario no afiliado: ' + destinations)
            else:
                destinos[Connections.gu.get_by_username(destinations)] = True

        else:
            if 'all' in destinations:
                for afiliado in Connections.gu:
                    destinos[afiliado] = True
            else:
                try:
                    for persona in destinations:
                        if persona not in Connections.gu.usernames:
                            raise UnrecognisedUsernameError('Usuario no afiliado: ' + str(destinations))
                        else:
                            destinos[Connections.gu.get_by_username(persona)] = True
                except TypeError:
                    logger.critical('"destinations" debe ser str o iterable, no ' + type(destinations).__name__)
                    raise TypeError('"destinations" debe ser str o iterable, no ' + type(destinations).__name__)

        threads = []
        for usuario in Connections.gu:
            if destinos[usuario] is False:
                continue
            if servicio not in usuario.servicios and force is False:
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
            report['destinations'] = self.errores
            report['code'] = 404
            logger.error('Errores en notificación: ' + str(report))
            return False
        else:
            return True

    def _notificar(self, usuario, title, message):
        # TODO: INCLUDE DOCSTRING
        # TODO: IMPROVE CODE
        # TODO: TRANSLATE INTO ENGLISH

        try:
            if usuario.esta_activo is False:
                logger.warning('[Usuario desactivado] ' + usuario.username)
                return False

            if Connections.DISABLE is True:
                logger.warning('[Notificaciones deshabilitadas] ' + usuario.username)
                return False
            else:
                usuario.launcher.fire(title, message)
                logger.debug('Enviada notificación a ' + usuario.username)
                return True
        except DownloaderError:
            self.append_error(usuario)

    @staticmethod
    def send_email(destinations, subject, message, files=None, is_file=False, origin='Rpi'):
        # TODO: INCLUDE DOCSTRING

        if isinstance(destinations, list) or isinstance(destinations, tuple):
            destinations = ', '.join(destinations)

        if files is not None:
            if isinstance(files, (tuple, list)):
                files = {x: None for x in files}
            else:
                files = {files: None}

        password = GestorClaves.get('mail_password')
        username = GestorClaves.get('mail_username')

        msg = MIMEMultipart()
        msg['From'] = f"{origin} <{username}>"
        msg['To'] = destinations
        msg['Subject'] = subject

        body = message.replace('\n', '<br>')
        msg.attach(MIMEText(body, 'html'))

        if files is not None:
            for i, file, realfilename in enumerate(files.items()):
                part = MIMEBase('application', "octet-stream")
                if is_file is False:
                    part.set_payload(open(file, "rb").read())
                else:
                    part.set_payload(file)
                encoders.encode_base64(part)

                if realfilename is None:
                    realfilename = f'Attachment_{i + 1}'

                part.add_header('Content-Disposition', 'attachment', filename=realfilename)

                msg.attach(part)
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(username, password)
        server.sendmail(username, msg['To'], msg.as_string())
        server.quit()
        return True

    @staticmethod
    def to_google_spreadsheets(filename, sheetname, data):
        # TODO: INCLUDE DOCSTRING

        logger.debug(f'Saving info to google spreadsheets - {filename} - {sheetname} - {data}')

        # Some stuff that needs to be done to use google sheets
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']

        credentials = Sac.from_json_keyfile_name(RpiDns.get('credenciales.googlesheets'), scope)
        gcc = gspread.authorize(credentials)

        try:
            archivo = gcc.open(filename)
        except SpreadsheetNotFound:
            logger.critical(f'File not found: {filename!r}')
            raise SpreadsheetNotFoundError(f'File not found: {filename!r}')

        try:
            wks = archivo.worksheet(sheetname)
        except WorksheetNotFound:
            logger.critical(f'Sheet not found: {sheetname!r}')
            raise SheetNotFoundError(f'Sheet not found: {sheetname!r}')

        wks.append_row(data)

    @staticmethod
    def from_google_spreadsheets(filename, sheetname):
        # TODO: INCLUDE DOCSTRING

        logger.debug(f'Getting info from google spreadsheets - {filename} - {sheetname}')

        # Some stuff that needs to be done to use google sheets

        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']

        credentials = Sac.from_json_keyfile_name(RpiDns.get('credenciales.googlesheets'), scope)
        gcc = gspread.authorize(credentials)

        try:
            archivo = gcc.open(filename)
        except SpreadsheetNotFound:
            logger.critical(f'File not found: {filename!r}')
            raise SpreadsheetNotFoundError(f'File not found: {filename!r}')

        try:
            wks = archivo.worksheet(sheetname)
        except WorksheetNotFound:
            logger.critical(f'Sheet not found: {sheetname!r}')
            raise SheetNotFoundError(f'Sheet not found: {sheetname!r}')

        return wks.get_all_records()
