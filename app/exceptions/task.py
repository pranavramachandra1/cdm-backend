from .base import AppError


class TaskError(AppError):
    pass


class TaskNotFoundError(TaskError):
    pass


class FailedToDeleteTaskError(TaskError):
    pass


class InvalidVersionRequest(TaskError):
    pass


class ToggleIncompleteError(TaskError):
    pass


class NoTasksToRemove(TaskError):
    pass
