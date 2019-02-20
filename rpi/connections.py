# -*- coding: utf-8 -*-
import logging
import os
import platform
import re
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
from .exceptions import NeccessaryArgumentError, UserNotFoundError, DownloaderError, \
    SpreadsheetNotFoundError, SheetNotFoundError, InvalidMailAddressError


class Connections:
    """Manages every outgoing connection."""
    DISABLE = platform.system() == 'Windows'

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.user_manager = UsersManager()

        self.errors_lock = Lock()
        self.codes_lock = Lock()
        self.errores = []
        self.output_codes = []
        self.downloader = Downloader()

    def append_code(self, code):
        with self.codes_lock:
            self.output_codes.append(code)

    def append_error(self, something):
        with self.errors_lock:
            self.errores.append(something)

    @staticmethod
    def force_notify(title, message, destinations=None):
        backup = Connections.DISABLE
        Connections.DISABLE = False
        output = Connections.notify(title, message, destinations, force=True)
        Connections.DISABLE = backup
        return output

    @staticmethod
    def notify(title, message, destinations=None, file=None, force=False):
        # TODO: INSERT DOCSTRING
        # TODO: IMPROVE CODE
        # TODO: TRANSLATE INTO ENGLISH

        self = object.__new__(Connections)
        self.__init__()
        self.logger.debug('Notify - %r, %r, %r, %r, %r', title, message, destinations, file, force)
        if force is True:
            self.DISABLE = False

        if destinations == 'multicast' and file is None:
            raise NeccessaryArgumentError("Multicast can't be used without the 'file' argument.")

        if destinations == 'broadcast' and force is False:
            raise PermissionError("'force' must be True in order to use broadcast.")

        if file is None and force is False:
            raise NeccessaryArgumentError(
                "The 'file' argument is needed in order to check permissions.")

        service = ServicesManager.get(file) if file is not None else ServicesManager.UNKNOWN

        passports = {x: False for x in self.user_manager}

        if isinstance(destinations, str):
            # If destination is 'broadcast', messaage is sent to
            # every user afiliated to the service.
            if destinations == 'multicast':
                for username in self.user_manager:
                    if service in username.services:
                        passports[username] = True

            if destinations == 'broadcast':
                for username in self.user_manager:
                    passports[username] = True

            passports[self.user_manager.get_by_username(destinations)] = True

        else:
            try:
                for persona in destinations:
                    passports[self.user_manager.get_by_username(persona)] = True
            except TypeError:
                self.logger.critical(
                    "'destinations' must be str or iterable, not %r",
                    destinations.__class__.__name__)
                raise TypeError(
                    f"'destinations' must be str or iterable, not "
                    f"{destinations.__class__.__name__!r}")

        # Checking validations of usernames (check that each username is registered at the database)
        for user in passports:
            if user.username not in self.user_manager.usernames:
                raise UserNotFoundError(f'Uknown username: {user.username!r}')

        threads = []
        for user in self.user_manager:
            if passports[user] is False:
                continue
            if service not in user.services and force is False:
                self.logger.warning(
                    'User %r is not registered in the service %r', user.username, service.name)
                continue

            self.logger.debug('Starting connection thread of %s', user.username)
            threads.append(
                Thread(name=user.username, target=self._notify, args=(user, title, message),
                       daemon=True))
            threads[-1].start()

        for thread in threads:
            thread.join()

        self.logger.debug('Connection threads finished')

        if len(self.errores):
            report = {'title': title, 'message': message, 'destinations': destinations,
                      'file': file, 'force': force}
            self.logger.error('Notification errors: %s', report)
            return False
        return all(self.output_codes)

    def _notify(self, user, title, message):
        # TODO: INCLUDE DOCSTRING
        # TODO: IMPROVE CODE
        # TODO: TRANSLATE INTO ENGLISH

        try:
            if user.is_active is False:
                self.logger.warning('BANNED USER: %r', user.username)
                self.append_code(False)
                return

            if self.DISABLE is True:
                self.logger.warning('DISABLED NOTIFICATIONS - %r', user.username)
                self.append_code(False)
                return
            try:
                user.launcher.fire(title, message)
            except NotImplementedError:
                self.append_code(False)
                return
            self.logger.debug('Sent notification to %r', user.username)
            self.append_code(True)
            return
        except DownloaderError:
            self.logger.error('Error sending to %s', user.username)
            self.append_error(user)
            self.append_code(True)

    @staticmethod
    def send_email(destinations, subject, message, files=None, is_file=False, origin='Rpi'):
        # TODO: INCLUDE DOCSTRING

        logger = logging.getLogger(__name__)
        logger.debug('Sending mail %r to %r', subject, destinations)

        address_pattern = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")

        if isinstance(destinations, (list, tuple)):
            for address in destinations:
                if address_pattern.search(address) is None:
                    logger.critical('%r is not a valid email address', address)
                    raise InvalidMailAddressError(f'{address!r} is not a valid email address.')
            destinations = ', '.join(destinations)

        if not isinstance(destinations, str):
            logger.critical('destinations must be iterable or str.')
            raise TypeError('destinations must be iterable or str.')

        if address_pattern.search(destinations) is None:
            logger.critical('%r is not a valid email address', destinations)
            raise InvalidMailAddressError(f'{destinations!r} is not a valid email address.')
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
                        logger.error('File not found: %r', file)
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

        logger = logging.getLogger(__name__)
        logger.debug('Saving info to google spreadsheets - %s - %s - %s', filename, sheetname, data)

        # Some stuff that needs to be done to use google sheets
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']

        credentials = Sac.from_json_keyfile_name(RpiDns.get('credenciales.googlesheets'), scope)
        gcc = gspread.authorize(credentials)

        try:
            archivo = gcc.open(filename)
        except SpreadsheetNotFound:
            logger.critical('Spreadsheet not found: %r', filename)
            raise SpreadsheetNotFoundError(f'Spreadsheet not found: {filename!r}')

        try:
            wks = archivo.worksheet(sheetname)
        except WorksheetNotFound:
            logger.critical('Sheet not found: %r', sheetname)
            raise SheetNotFoundError(f'Sheet not found: {sheetname!r}')

        wks.append_row(data)

    @staticmethod
    def from_google_spreadsheets(filename, sheetname):
        # TODO: INCLUDE DOCSTRING

        logger = logging.getLogger(__name__)
        logger.debug('Getting info from google spreadsheets - %s - %s', filename, sheetname)

        # Some stuff that needs to be done to use google sheets

        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']

        credentials = Sac.from_json_keyfile_name(RpiDns.get('credenciales.googlesheets'), scope)
        gcc = gspread.authorize(credentials)

        try:
            archivo = gcc.open(filename)
        except SpreadsheetNotFound:
            logger.critical('Spreadsheet not found: %r', filename)
            raise SpreadsheetNotFoundError(f'Spreadsheet not found: {filename!r}')

        try:
            wks = archivo.worksheet(sheetname)
        except WorksheetNotFound:
            logger.critical('Sheet not found: %r', sheetname)
            raise SheetNotFoundError(f'Sheet not found: {sheetname!r}')

        return wks.get_all_records()
