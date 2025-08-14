from .base import AppError


class ListError(AppError):
    pass


class ListNotFoundError(ListError):
    pass


class FailedToDeleteList(ListError):
    pass


class InvalidParameters(ListError):
    pass
