# -*- coding: utf-8 -*-
import os
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

from rpi.managers.keys_manager import KeysManager
from rpi.managers.services_manager import ServicesManager
from rpi.managers.users_manager import UsersManager
from .dns import RpiDns
from .downloader import Downloader
from .exceptions import NeccessaryArgumentError, UnrecognisedUsernameError, DownloaderError, \
    SpreadsheetNotFoundError, SheetNotFoundError
from .rpi_logging import Logging

debug_lock = Lock()


class Connections:
    """Manages every outgoing connection."""
    DISABLE = platform.system() == 'Windows'

    def __init__(self):
        self.logger = Logging.get(__file__, __name__)
        self.gu = UsersManager()

        self.lock = Lock()
        self.errores = []
        self._downloader = Downloader()

    def append_error(self, something):
        with self.lock:
            self.errores.append(something)

    @staticmethod
    def force_notify(title, message, destinations=None):
        backup = Connections.DISABLE
        Connections.DISABLE = False
        output = Connections.notify(title, message, destinations, force=True)
        Connections.DISABLE = backup
        return output

    @staticmethod
    def notify(title, message, destinations=None, file: dict = None, force=False):
        # TODO: INSERT DOCSTRING
        # TODO: IMPROVE CODE
        # TODO: TRANSLATE INTO ENGLISH

        self = object.__new__(Connections)
        self.__init__()
        self.logger.debug(f'Notify - {title!r}, {message!r}, {destinations!r}, {file!r}, {force!r}')

        if file is None and force is False:
            raise NeccessaryArgumentError("The 'file' argument is needed in order to check permissions.")

        if destinations == 'broadcast' and file is None:
            raise NeccessaryArgumentError("Broadcast can't be used without the 'file' argument.")

        service = ServicesManager.get(file) if file is not None else ServicesManager.UNKNOWN

        passports = {x: False for x in self.gu}

        if isinstance(destinations, str):
            # Si el user destinations es 'broadcast', se manda a todos los usuarios afiliados al servicio.
            if destinations == 'broadcast':
                for username in self.gu:
                    if service in username.services:
                        passports[username] = True

            passports[self.gu.get_by_username(destinations)] = True

        else:
            try:
                for persona in destinations:
                    passports[self.gu.get_by_username(persona)] = True
            except TypeError:
                self.logger.critical(f"'destinations' must be str or iterable, not {destinations.__class__.__name__!r}")
                raise TypeError(f"'destinations' must be str or iterable, not {destinations.__class__.__name__!r}")

        # Checking validations of usernames (check that each username is registered at the database)
        for user in passports:
            if user.username not in self.gu.usernames:
                raise UnrecognisedUsernameError(f'Uknown username: {user.username!r}')

        threads = []
        for user in self.gu:
            if passports[user] is False:
                continue
            if service not in user.services and force is False:
                self.logger.warning(f'User {user.username!r} is not registered in the service {service.name!r}')
                continue

            self.logger.debug(f'Starting connection thread of {user.username!r}')
            threads.append(Thread(name=user.username, target=self._notify, args=(user, title, message), daemon=True))
            threads[-1].start()

        for thread in threads:
            thread.join()

        self.logger.debug('Connection threads finished')

        if len(self.errores) > 0:
            report = {'title': title, 'message': message, 'destinations': destinations, 'file': file, 'force': force}
            self.logger.error(f'Notification errors: {report}')
            return False
        else:
            return True

    def _notify(self, user, title, message):
        # TODO: INCLUDE DOCSTRING
        # TODO: IMPROVE CODE
        # TODO: TRANSLATE INTO ENGLISH

        try:
            if user.is_active is False:
                self.logger.warning(f'BANNED USER: {user.username!r}')
                return False

            if self.DISABLE is True:
                self.logger.warning(f'DISABLED NOTIFICATIONS - {user.username!r}')
                return False
            else:
                user.launcher.fire(title, message)
                self.logger.debug(f'Sent notification to {user.username!r}')
                return True
        except DownloaderError:
            self.append_error(user)

    @staticmethod
    def send_email(destinations, subject, message, files=None, is_file=False, origin='Rpi'):
        # TODO: INCLUDE DOCSTRING

        if isinstance(destinations, list) or isinstance(destinations, tuple):
            destinations = ', '.join(destinations)

        try:
            if len(files) == 0:
                files = None
        except TypeError:
            pass

        if files is not None:
            if isinstance(files, (tuple, list)):
                if is_file is False:
                    files = {x: os.path.basename(x) for x in files}
                else:
                    files = {x: None for x in files}
            elif isinstance(files, dict):
                pass
            elif isinstance(files, str):
                if is_file is False:
                    files = {files: os.path.basename(files)}
                else:
                    files = {files: None}
            else:
                raise TypeError

        password = KeysManager.get('mail_password')
        username = KeysManager.get('mail_username')

        msg = MIMEMultipart()
        msg['From'] = f"{origin} <{username}>"
        msg['To'] = destinations
        msg['Subject'] = subject

        body = message.replace('\n', '<br>')
        msg.attach(MIMEText(body, 'html'))

        if files is not None:
            for i, (file, realfilename) in enumerate(files.items()):
                part = MIMEBase('application', "octet-stream")
                if is_file is False:
                    try:
                        part.set_payload(open(file, "rb").read())
                    except FileNotFoundError:
                        continue
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

        logger = Logging.get(__file__, __name__)
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

        logger = Logging.get(__file__, __name__)
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
