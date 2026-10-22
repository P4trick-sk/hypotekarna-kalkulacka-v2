"""Jednotný formát chýb API: {"errors": [{"field", "code", "message"}]}."""

from __future__ import annotations

from pydantic import BaseModel

from calc import ValidationError


class ErrorItem(BaseModel):
    field: str | None = None
    code: str
    message: str


class ErrorResponse(BaseModel):
    errors: list[ErrorItem]


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.items = [ErrorItem(field=field, code=code, message=message)]


class InputInvalid(ApiError):
    """422 z doménovej validácie (`calc.validate`)."""

    def __init__(self, errors: list[ValidationError]) -> None:
        Exception.__init__(self, errors[0].message)
        self.status = 422
        self.items = [ErrorItem(field=e.field, code=e.code, message=e.message) for e in errors]


def not_found(message: str = "Nenašlo sa.") -> ApiError:
    return ApiError(404, "not_found", message)
