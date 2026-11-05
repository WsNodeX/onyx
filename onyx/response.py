"""The :class:`Response` object returned by handlers.

A handler may return a :class:`Response` directly, or the framework will wrap
plain ``str`` / ``dict`` / ``bytes`` values automatically (see ``app.py``).
"""
from __future__ import annotations

import json
from typing import Dict, Optional, Union

from .datastructures import Headers, build_set_cookie

_DEFAULT_STATUS_TEXT = {
    200: "OK",
    201: "Created",
    204: "No Content",
    301: "Moved Permanently",
    302: "Found",
    303: "See Other",
    304: "Not Modified",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    409: "Conflict",
    422: "Unprocessable Entity",
    500: "Internal Server Error",
    503: "Service Unavailable",
}


class Response:
    """Holds the status, headers, cookies and body of an HTTP response."""

    def __init__(
        self,
        body: Union[str, bytes] = "",
        status_code: int = 200,
        *,
        headers: Optional[Dict[str, str]] = None,
        content_type: str = "text/plain; charset=utf-8",
    ) -> None:
        self.status_code = status_code
        self.headers = Headers()
        if headers:
            for k, v in headers.items():
                self.headers.set(k, v)
        if content_type and "content-type" not in self.headers:
            self.headers.set("content-type", content_type)
        self.body = body.encode("utf-8") if isinstance(body, str) else bytes(body)
        self._cookies: Dict[str, str] = {}

    # --- constructors ----------------------------------------------------
    @classmethod
    def text(cls, body: str, status_code: int = 200, **kw) -> "Response":
        return cls(body, status_code, content_type="text/plain; charset=utf-8", **kw)

    @classmethod
    def html(cls, body: str, status_code: int = 200, **kw) -> "Response":
        return cls(body, status_code, content_type="text/html; charset=utf-8", **kw)

    @classmethod
    def json(cls, data: object, status_code: int = 200, **kw) -> "Response":
        body = json.dumps(data, ensure_ascii=False)
        return cls(
            body, status_code, content_type="application/json; charset=utf-8", **kw
        )

    @classmethod
    def redirect(cls, location: str, status_code: int = 302) -> "Response":
        resp = cls("", status_code, content_type="text/html; charset=utf-8")
        resp.headers.set("location", location)
        return resp

    # --- cookies ---------------------------------------------------------
    def set_cookie(
        self,
        name: str,
        value: str,
        *,
        max_age: Optional[int] = None,
        path: str = "/",
        domain: Optional[str] = None,
        secure: bool = False,
        httponly: bool = False,
        samesite: Optional[str] = None,
    ) -> None:
        self._cookies[name] = build_set_cookie(
            name,
            value,
            max_age=max_age,
            path=path,
            domain=domain,
            secure=secure,
            httponly=httponly,
            samesite=samesite,
        )

    def delete_cookie(self, name: str, *, path: str = "/") -> None:
        self.set_cookie(name, "", max_age=0, path=path)

    # --- serialization ---------------------------------------------------
    @property
    def status_line(self) -> str:
        text = _DEFAULT_STATUS_TEXT.get(self.status_code, "OK")
        return f"{self.status_code} {text}"

    def header_list(self) -> list:
        """Return ``[(name, value), ...]`` including Set-Cookie headers."""
        items = list(self.headers.items())
        for cookie in self._cookies.values():
            items.append(("Set-Cookie", cookie))
        return items

    def render_headers(self) -> bytes:
        lines = []
        for key, value in self.headers.items():
            lines.append(f"{key}: {value}")
        for cookie in self._cookies.values():
            lines.append(f"Set-Cookie: {cookie}")
        return ("\r\n".join(lines)).encode("latin-1", "replace")

    @property
    def data(self) -> bytes:
        return self.body

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"<Response {self.status_code}>"
