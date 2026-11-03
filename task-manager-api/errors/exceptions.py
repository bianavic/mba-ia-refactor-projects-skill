"""Typed errors; the central handler turns them into responses."""


class AppError(Exception):
    status = 500

    def __init__(self, message, status=None):
        super().__init__(message)
        self.message = message
        if status is not None:
            self.status = status

    def body(self):
        return {"error": self.message}


class ValidationError(AppError):
    status = 400


class Unauthorized(AppError):
    status = 401


class Forbidden(AppError):
    status = 403


class NotFound(AppError):
    status = 404


class Conflict(AppError):
    status = 409
