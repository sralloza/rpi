# -*- coding: utf-8 -*-

"""Exceptions raised by elements of the rpi module."""


# ERRORS


class BaseError(Exception):
    """Base class for errors in the system."""


class InvalidMailAddressError(BaseError):
    """Invalid mail address."""


class WrongCalledError(BaseError):
    """A method, class or function has been used wrongly."""


class InvalidArgumentError(BaseError):
    """An invalid argument has been passed."""


class NeccessaryArgumentError(BaseError):
    """A neccessary argument is missing."""


class UnrecognisedServiceError(BaseError):
    """A service couldn't be identified."""


class UserNotFoundError(BaseError):
    """A username couldn't be identified."""


class UserError(BaseError):
    """User error."""


class DnsError(BaseError):
    """DNS error."""


class InvalidLauncherError(BaseError):
    """The launcher is not supported."""


class InvalidLanguage(BaseError):
    """The language is not valid."""


class MailError(BaseError):
    """Mail error."""


class MissingKeyError(BaseError):
    """A key can not be found."""


class PlatformError(BaseError):
    """Can not be executed in this platform."""


class AuxiliarFileError(BaseError):
    """The auxiliar file can not be executed, only imported."""


class InvalidMonthError(BaseError):
    """Invalid month."""


class InvalidDayError(BaseError):
    """Invalid day."""


class WrongLogType(BaseError):
    """The log specified is not correct."""


class UnknownError(BaseError):
    """The error is so catastrophic that can't be identified."""


class DownloaderError(BaseError):
    """Error while downloading."""


class CrontabError(BaseError):
    """Error in crontab"""


class JobNotFoundError(BaseError):
    """Job can't be found."""


class ExistingJobError(BaseError):
    """The job does exist."""


class UnableToSave(BaseError):
    """Cant be saved."""


class ConfigError(BaseError):
    """General configuration error."""


class ConfigNotFoundError(ConfigError):
    """Configuration not found."""


class EmptyConfigError(ConfigError):
    """There is no config to save."""


class MissingOptionsError(BaseError):
    """Options must be selected."""


class InvalidOptionError(BaseError):
    """The option is not valid."""


class SpreadsheetNotFoundError(BaseError):
    """Sheet not found."""


class SheetNotFoundError(BaseError):
    """Sheet not found."""


# WARNINGS

class BaseWarning(Warning):
    """Base class for warnings."""


class TooLowAccuracy(BaseWarning):
    """When finding DNS address, precision is lower than 0.5."""


class ExistingMenuWarning(BaseWarning):
    """The menu already exists."""


class NotEnoughSubjectsWarning(BaseWarning):
    """Not enough subjects have been found."""


class UnrecognisedServiceWarning(BaseWarning):
    """A service couldnt be identified."""


class UnexpectedBehaviourWarning(BaseWarning):
    """This is an expected situation, but its not critical."""
