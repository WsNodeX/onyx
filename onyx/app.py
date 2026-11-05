"""The :class:`Onyx` application object.

This ties together routing, middleware, error handling and the request
lifecycle. It is intentionally small: one ``handle(request)`` method does the
real work, and both the WSGI entrypoint and the test client funnel through it.
"""
from __future__ import annotations

import traceback
from typing import Callable, Dict, List, Optional, Tuple

from .blueprint import Blueprint
from .datastructures import Headers
from .errors import HTTPError, InternalServerError, MethodNotAllowed
from .middleware import build_chain
from .request import Request
from .response import Response
from .router import Router


class Onyx:
    """A composable, zero-dependency web application."""

    def __init__(self, name: str = "onyx", *, debug: bool = False) -> None:
        self.name = name
        self.debug = debug
        self.router = Router()
        self.middlewares: List = []
        self._error_handlers: Dict[type, Callable] = {}

    # --- routing ---------------------------------------------------------
    def route(
        self,
        pattern: str,
        methods: Optional[List[str]] = None,
        name: Optional[str] = None,
    ):
        methods = methods or ["GET"]

        def decorator(handler: Callable) -> Callable:
            self.router.add(pattern, methods, handler, name)
            return handler

        return decorator

    def get(self, pattern: str, name: Optional[str] = None):
        return self.route(pattern, ["GET"], name)

    def post(self, pattern: str, name: Optional[str] = None):
        return self.route(pattern, ["POST"], name)

    def put(self, pattern: str, name: Optional[str] = None):
        return self.route(pattern, ["PUT"], name)

    def delete(self, pattern: str, name: Optional[str] = None):
        return self.route(pattern, ["DELETE"], name)

    def patch(self, pattern: str, name: Optional[str] = None):
        return self.route(pattern, ["PATCH"], name)

    def head(self, pattern: str, name: Optional[str] = None):
        return self.route(pattern, ["HEAD"], name)

    def options(self, pattern: str, name: Optional[str] = None):
        return self.route(pattern, ["OPTIONS"], name)

    def register_blueprint(self, bp: Blueprint) -> None:
        bp.register_on(self)

    # --- middleware & errors --------------------------------------------
    def add_middleware(self, middleware) -> None:
        self.middlewares.append(middleware)

    def use(self, middleware) -> None:
        self.add_middleware(middleware)

    def errorhandler(self, exc_class: type):
        def decorator(handler: Callable) -> Callable:
            self._error_handlers[exc_class] = handler
            return handler

        return decorator

    # --- request lifecycle ----------------------------------------------
    def handle(self, request: Request) -> Response:
        try:
            handler, params = self.router.resolve(request.method, request.path)
            request.path_params = params
            chain = build_chain(
                self.middlewares,
                lambda req: self._invoke(handler, req),
            )
            result = chain(request)
            return self._ensure_response(result)
        except HTTPError as exc:
            return self._handle_http_error(exc)
        except Exception as exc:  # noqa: BLE001 - top-level safety net
            return self._handle_exception(exc)

    def _invoke(self, handler: Callable, request: Request) -> Response:
        return self._ensure_response(handler(request))

    # --- response coercion ----------------------------------------------
    def _ensure_response(self, result) -> Response:
        if result is None:
            return Response(
                "Handler returned None; a Response object is required", 500
            )
        if isinstance(result, Response):
            return result
        if isinstance(result, tuple):
            data = result[0] if len(result) > 0 else ""
            status = result[1] if len(result) > 1 else 200
            headers = result[2] if len(result) > 2 else None
            return self._wrap_data(data, status, headers)
        return self._wrap_data(result, 200, None)

    def _wrap_data(self, data, status: int, headers: Optional[Dict[str, str]]) -> Response:
        if isinstance(data, dict):
            return Response.json(data, status, headers=headers)
        if isinstance(data, bytes):
            resp = Response(
                data, status, headers=headers,
                content_type="application/octet-stream",
            )
            return resp
        if isinstance(data, str):
            return Response.text(data, status, headers=headers)
        return Response.text(str(data), status, headers=headers)

    # --- error handling --------------------------------------------------
    def _handle_http_error(self, exc: HTTPError) -> Response:
        handler = self._find_error_handler(type(exc))
        if handler is not None:
            return self._ensure_response(handler(exc))
        body = exc.as_response_body()
        resp = Response(
            body, exc.status_code, content_type="application/json; charset=utf-8"
        )
        # MethodNotAllowed carries the set of permitted methods; surface it
        # as an RFC-compliant Allow header.
        if isinstance(exc, MethodNotAllowed) and exc.allowed_methods:
            resp.headers.set("Allow", ", ".join(exc.allowed_methods))
        for key, value in exc.headers.items():
            resp.headers.set(key, value)
        return resp

    def _handle_exception(self, exc: Exception) -> Response:
        handler = self._find_error_handler(type(exc)) or self._find_error_handler(
            Exception
        )
        if handler is not None:
            return self._ensure_response(handler(exc))
        detail = "Internal Server Error"
        if self.debug:
            detail = traceback.format_exc()
        return Response.json(
            {"error": "InternalServerError", "detail": detail}, 500
        )

    def _find_error_handler(self, exc_type: type):
        # Walk the MRO so a handler registered for a parent class is found.
        for klass in exc_type.__mro__:
            handler = self._error_handlers.get(klass)
            if handler is not None:
                return handler
        return None

    # --- WSGI ------------------------------------------------------------
    def __call__(self, environ, start_response):
        request = self._from_wsgi(environ)
        response = self.handle(request)
        status = response.status_line
        headers = response.header_list()
        start_response(status, headers)
        return [response.body]

    def _from_wsgi(self, environ) -> Request:
        method = environ.get("REQUEST_METHOD", "GET")
        path = environ.get("PATH_INFO", "/") or "/"
        query_string = environ.get("QUERY_STRING", "")
        scheme = environ.get("wsgi.url_scheme", "http")
        client = environ.get("REMOTE_ADDR")
        headers = Headers()
        for key, value in environ.items():
            if key.startswith("HTTP_"):
                name = key[5:].replace("_", "-").title()
                headers.add(name, value)
            elif key in ("CONTENT_TYPE", "CONTENT_LENGTH"):
                headers.add(key.replace("_", "-").title(), value)
        try:
            length = int(environ.get("CONTENT_LENGTH") or 0)
        except ValueError:
            length = 0
        body = b""
        if length > 0:
            body = environ.get("wsgi.input").read(length)
        return Request(
            method,
            path,
            headers=headers,
            body=body,
            scheme=scheme,
            query_string=query_string,
            client=client,
        )

    # --- dev server & test client ---------------------------------------
    def run(self, host: str = "127.0.0.1", port: int = 8000, *, debug: bool = False) -> None:
        from .server import make_server

        self.debug = debug
        srv = make_server(self, host=host, port=port)
        print(f"Onyx '{self.name}' serving on http://{host}:{port}  (Ctrl+C to stop)")
        try:
            srv.serve_forever()
        except KeyboardInterrupt:  # pragma: no cover - interactive only
            srv.shutdown()

    def test_client(self):
        from .testing import TestClient

        return TestClient(self)
