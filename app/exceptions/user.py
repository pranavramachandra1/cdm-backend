from .base import AppError


class UserError(AppError):
    pass


class UserNotFoundError(UserError):
    pass


class UserAlreadyExistsError(UserError):
    pass


class InvalidCredentialsError(UserError):
    pass
