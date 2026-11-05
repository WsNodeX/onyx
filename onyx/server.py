"""A tiny dependency-free development server.

It speaks enough of HTTP/1.1 to serve a framework app during local
development: it reads the request line, headers and body, hands a fully
populated :class:`~onyx.request.Request` to ``app.handle``, then writes the
response back. Production deployments should sit behind a real WSGI server
(``app`` is a valid WSGI callable), but this is enough to try things locally.
"""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional

from .datastructures import Headers
from .request import Request
from .response import Response, _DEFAULT_STATUS_TEXT


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "Onyx/1.0"

    # Silence the default request logging for a cleaner dev experience.
    def log_message(self, *args, **kwargs) -> None:  # pragma: no cover
        return

    def _build_request(self) -> Request:
        raw_path, _, query_string = self.path.partition("?")
        headers = Headers()
        for key in self.headers.keys():
            headers.add(key, self.headers.get(key))
        try:
            length = int(self.headers.get("Content-Length", 0) or 0)
        except ValueError:
            length = 0
        body = self.rfile.read(length) if length > 0 else b""
        return Request(
            self.command,
            raw_path or "/",
            headers=headers,
            body=body,
            scheme="http",
            query_string=query_string,
            client=self.client_address[0],
        )

    def _write_response(self, response: Response) -> None:
        message = _DEFAULT_STATUS_TEXT.get(response.status_code, "OK")
        self.send_response_only(response.status_code, message)
        for key, value in response.header_list():
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(response.body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(response.body)
        # Close each connection for simplicity in a dev server.
        self.close_connection = True

    def _dispatch(self) -> None:
        request = self._build_request()
        try:
            response = self.server.app.handle(request)  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001 - never let the server crash
            response = Response("Internal Server Error", 500)
        self._write_response(response)

    def do_GET(self) -> None:  # noqa: N802
        self._dispatch()

    def do_POST(self) -> None:  # noqa: N802
        self._dispatch()

    def do_PUT(self) -> None:  # noqa: N802
        self._dispatch()

    def do_DELETE(self) -> None:  # noqa: N802
        self._dispatch()

    def do_PATCH(self) -> None:  # noqa: N802
        self._dispatch()

    def do_HEAD(self) -> None:  # noqa: N802
        self._dispatch()

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._dispatch()


def make_server(app, host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    """Create (but do not start) a dev server hosting ``app``."""
    httpd = ThreadingHTTPServer((host, port), _Handler)
    httpd.app = app  # type: ignore[attr-defined]
    return httpd


def serve(app, host: str = "127.0.0.1", port: int = 8000) -> None:  # pragma: no cover
    """Block and serve ``app`` until interrupted."""
    httpd = make_server(app, host=host, port=port)
    print(f"Serving on http://{host}:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()
