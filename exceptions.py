# -*- coding: utf-8 -*-

# ERRORES


class BaseError(Exception):
    """Clase base de errores."""


class WrongCalledError(BaseError):
    """Se ha usado un método, clase, o función de una manera errónea."""


class InvalidArgumentError(BaseError):
    """Se ha pasado un argumento inválido."""


class NeccessaryArgumentError(BaseError):
    """Un argumento necesario no se ha pasado."""


class UnrecognisedServiceError(BaseError):
    """No se ha reconocido un servicio."""


class UnrecognisedUsernameError(BaseError):
    """No se ha reconocido un nombre de usuario."""


class DnsError(BaseError):
    """Error de DNS"""


class InvalidLauncherError(BaseError):
    """El launcher no está soportado"""


class PasswordKeyError(BaseError):
    """Clase base para errores de claves."""


class MailError(BaseError):
    """Error con mail."""


class MissingKeyError(PasswordKeyError):
    """No se encuentra una clave."""


class PlatformError(BaseError):
    """No se puede ejecutar en esta plataforma."""


class AuxiliarFileError(BaseError):
    """El archivo no se puede ejecutar, sólo contiene código auxiliar."""


class InvalidMonthError(BaseError):
    """El mes insertado no es correcto."""


class InvalidDayError(BaseError):
    """El día insertado no es correcto."""


class WrongLogType(BaseError):
    """El tipo especificado no es correcto."""


class UnknownError(BaseError):
    """No se sabe qué ha podido pasar."""


class ApiError(BaseError):
    """Ha habido un error con una API."""


class DownloaderError(BaseError):
    """Error al descargar."""


class JobNotFoundError(BaseError):
    """No se encuentra el job."""


class ExistingJobError(BaseError):
    """Existe el job."""


class UnableToSave(BaseError):
    """No se puede guardar"""


class ConfigNotFoundError(BaseError):
    """Configuración no encontrada."""


class EmptyConfigError(BaseError):
    """No hay configuración que guardar."""


class MissingOptionsError(BaseError):
    """No se han especificado las opciones."""


class InvalidOptionError(BaseError):
    """La opción no es válida."""


# WARNINGS

class BaseWarning(Warning):
    """Clase base para los warnings declarados."""


class TooLowAccuracy(BaseWarning):
    """Se lanza si se ha encontrado la dirección DNS con menos de un 50% de precisión."""


class ExistingMenuWarning(BaseWarning):
    """Se lanza si se quiere almacenar un menú ya almacenado."""


class NotEnoughSubjectsWarning(BaseWarning):
    """No se han encontrado suficientes asignaturas."""


class UnrecognisedServiceWarning(BaseWarning):
    """No se ha reconocido un servicio."""


class UnexpectedBehaviourWarning(BaseWarning):
    """No debería haberse dado esta situación, pero no se sabe si es crítica."""
