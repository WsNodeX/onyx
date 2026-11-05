"""Onyx — a zero-dependency Python micro web framework.

Everything you need to build an HTTP service lives in this package. There are
no third-party requirements: routing, middleware, request/response objects,
a WSGI entrypoint, an offline test client and a small development server are
all implemented in pure Python.

Typical usage::

    from onyx import Onyx, Response

    app = Onyx()

    @app.get("/hello/<name>")
    def hello(request):
        return Response.json({"hello": request.path_params["name"]})

    if __name__ == "__main__":
        app.run(port=8000)
"""
from __future__ import annotations

from .app import Onyx
from .blueprint import Blueprint
from .errors import (
    BadRequest,
    Conflict,
    Forbidden,
    HTTPError,
    InternalServerError,
    MethodNotAllowed,
    NotFound,
    ServiceUnavailable,
    Unauthorized,
    UnprocessableEntity,
    from_status,
)
from .middleware import Middleware
from .request import Request
from .response import Response
from .testing import TestClient

__version__ = "1.0.0"

__all__ = [
    "Onyx",
    "Blueprint",
    "Request",
    "Response",
    "TestClient",
    "Middleware",
    "HTTPError",
    "BadRequest",
    "Unauthorized",
    "Forbidden",
    "NotFound",
    "MethodNotAllowed",
    "Conflict",
    "UnprocessableEntity",
    "InternalServerError",
    "ServiceUnavailable",
    "from_status",
    "__version__",
]
