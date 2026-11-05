"""HTTP error types used across the framework.

Every exception raised inside a handler that derives from :class:`HTTPError`
carries a concrete status code, so the application can translate it into a
real HTTP response without guessing.
"""
from __future__ import annotations

from typing import Dict, Optional, Union


class HTTPError(Exception):
    """Base class for any error that maps to an HTTP status code."""

    status_code: int = 500
    default_detail: str = "Internal Server Error"

    def __init__(
        self,
        detail: Optional[str] = None,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        super().__init__(detail or self.default_detail)
        self.detail = detail or self.default_detail
        self.headers: Dict[str, str] = dict(headers or {})

    def as_response_body(self) -> bytes:
        """Render a small JSON problem document for the client."""
        import json

        payload = {"error": self.__class__.__name__, "detail": self.detail}
        return json.dumps(payload, ensure_ascii=False).encode("utf-8")


class BadRequest(HTTPError):
    status_code = 400
    default_detail = "Bad Request"


class Unauthorized(HTTPError):
    status_code = 401
    default_detail = "Unauthorized"


class Forbidden(HTTPError):
    status_code = 403
    default_detail = "Forbidden"


class NotFound(HTTPError):
    status_code = 404
    default_detail = "Not Found"


class MethodNotAllowed(HTTPError):
    status_code = 405
    default_detail = "Method Not Allowed"

    def __init__(
        self,
        allowed_methods: Optional[Union[list, tuple, set]] = None,
        detail: Optional[str] = None,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        super().__init__(detail, headers=headers)
        self.allowed_methods = [m.upper() for m in (allowed_methods or [])]

    def as_response_body(self) -> bytes:
        import json

        payload = {
            "error": self.__class__.__name__,
            "detail": self.detail,
            "allowed": self.allowed_methods,
        }
        return json.dumps(payload, ensure_ascii=False).encode("utf-8")


class Conflict(HTTPError):
    status_code = 409
    default_detail = "Conflict"


class UnprocessableEntity(HTTPError):
    status_code = 422
    default_detail = "Unprocessable Entity"


class InternalServerError(HTTPError):
    status_code = 500
    default_detail = "Internal Server Error"


class ServiceUnavailable(HTTPError):
    status_code = 503
    default_detail = "Service Unavailable"


# Convenient registry so the application can build the right class from a code.
_STATUS_MAP: Dict[int, type] = {
    400: BadRequest,
    401: Unauthorized,
    403: Forbidden,
    404: NotFound,
    405: MethodNotAllowed,
    409: Conflict,
    422: UnprocessableEntity,
    500: InternalServerError,
    503: ServiceUnavailable,
}


def from_status(status_code: int, detail: Optional[str] = None) -> HTTPError:
    """Return an :class:`HTTPError` subclass matching ``status_code``."""
    cls = _STATUS_MAP.get(status_code, HTTPError)
    return cls(detail)
