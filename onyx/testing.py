"""An offline test client.

It sends requests straight into ``app.handle`` with no sockets involved, which
keeps unit tests fast and deterministic while exercising the full middleware
and routing stack exactly as a real request would.
"""
from __future__ import annotations

import json as json_module
from typing import Any, Dict, Optional
from urllib.parse import urlencode

from .datastructures import Headers, parse_cookie
from .request import Request
from .response import Response


class _Response:
    """Thin adapter over a framework :class:`Response` for assertions."""

    def __init__(self, response: Response) -> None:
        self._resp = response
        self.status_code = response.status_code
        self.headers = response.headers
        self._text = response.body.decode("utf-8", "replace")
        self.content = response.body
        self.cookies = self._parse_cookies(response)

    @staticmethod
    def _parse_cookies(response: Response) -> Dict[str, str]:
        out: Dict[str, str] = {}
        for key, value in response.header_list():
            if key.lower() != "set-cookie":
                continue
            first = value.split(";", 1)[0]
            if "=" in first:
                name, _, val = first.partition("=")
                out[name.strip()] = val.strip()
        return out

    @property
    def text(self) -> str:
        return self._text

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    def json(self) -> Any:
        if not self._text:
            return None
        return json_module.loads(self._text)

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"<TestResponse {self.status_code}>"


class TestClient:
    """Drive an :class:`~onyx.app.Onyx` app from tests or a REPL."""

    def __init__(self, app) -> None:
        self.app = app

    def request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        data: Any = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> _Response:
        if "?" in path:
            raw_path, _, query_string = path.partition("?")
        else:
            raw_path, query_string = path, ""
        http_headers = Headers()
        if headers:
            for k, v in headers.items():
                http_headers.set(k, v)

        body = b""
        if json is not None:
            body = json_module.dumps(json, ensure_ascii=False).encode("utf-8")
            if "content-type" not in http_headers:
                http_headers.set("content-type", "application/json; charset=utf-8")
        elif data is not None:
            if isinstance(data, dict):
                body = urlencode(data).encode("utf-8")
                if "content-type" not in http_headers:
                    http_headers.set(
                        "content-type", "application/x-www-form-urlencoded"
                    )
            elif isinstance(data, str):
                body = data.encode("utf-8")
            elif isinstance(data, (bytes, bytearray)):
                body = bytes(data)

        if cookies:
            cookie_header = "; ".join(f"{k}={v}" for k, v in cookies.items())
            http_headers.set("cookie", cookie_header)

        request = Request(
            method,
            raw_path or "/",
            headers=http_headers,
            body=body,
            query_string=query_string,
        )
        return _Response(self.app.handle(request))

    def get(self, path: str, **kw) -> _Response:
        return self.request("GET", path, **kw)

    def post(self, path: str, **kw) -> _Response:
        return self.request("POST", path, **kw)

    def put(self, path: str, **kw) -> _Response:
        return self.request("PUT", path, **kw)

    def delete(self, path: str, **kw) -> _Response:
        return self.request("DELETE", path, **kw)

    def patch(self, path: str, **kw) -> _Response:
        return self.request("PATCH", path, **kw)

    def head(self, path: str, **kw) -> _Response:
        return self.request("HEAD", path, **kw)

    def options(self, path: str, **kw) -> _Response:
        return self.request("OPTIONS", path, **kw)
