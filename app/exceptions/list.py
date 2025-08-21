from .base import AppError


class ListError(AppError):
    pass


class ListNotFoundError(ListError):
    pass


class FailedToDeleteList(ListError):
    pass


class InvalidParameters(ListError):
    pass

class ListVisibilityToggleError(ListError):
    """
    Error is raised when there is a mismatch in the state of 
    visibility with a list.
    """
    pass

class ListAuthenticationError(ListError):
    """
    User is not allowed to access list
    """
