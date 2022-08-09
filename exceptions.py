class MNException(Exception):
    pass


class ModelValidationError(MNException):
    def __init__(self, fp):
        self.fp = fp

    def __str__(self):
        return f"Could not validate property: {self.fp}"


class DBException(MNException):
    pass


class EntryNotFoundError(DBException):
    pass


class EntryExistsError(DBException):
    pass


class AuthException(MNException):
    def __init__(self, **kwargs):
        self.user = kwargs.pop('user', None)


class InvalidUsernameError(AuthException):
    pass


class InvalidPasswordError(AuthException):
    pass


class UsernameUsedError(AuthException):
    pass


class EmailUsedError(AuthException):
    pass


class FieldValidationError(AuthException):
    pass


class UserStateError(AuthException):
    pass


class FileException(MNException):
    pass


class TransformationError(FileException):
    pass
