"""The :class:`Request` object handed to every handler.

It lazily parses query strings, JSON bodies, form data and cookies so that a
handler only pays for what it actually reads.
"""
from __future__ import annotations

import json
from typing import Any, Dict, Optional

from .datastructures import (
    Headers,
    MultiDict,
    parse_cookie,
    parse_query_string,
)


class _Unset:
    """Sentinel distinguishing 'not parsed yet' from 'parsed as None'."""

    def __repr__(self) -> str:  # pragma: no cover
        return "<unset>"


_UNSET = _Unset()


class Request:
    """Immutable-ish wrapper around a single HTTP request."""

    def __init__(
        self,
        method: str,
        path: str,
        *,
        headers: Optional[Headers] = None,
        body: bytes = b"",
        scheme: str = "http",
        query_string: str = "",
        client: Optional[str] = None,
    ) -> None:
        self.method = method.upper()
        self.path = path
        self.headers = headers or Headers()
        self.body = body
        self.scheme = scheme
        self.query_string = query_string
        self.client = client
        self._query: Optional[MultiDict] = None
        self._cookies: Optional[Dict[str, str]] = None
        self._json: Any = _UNSET
        self._form: Optional[MultiDict] = None
        # Path params captured by the router are attached by the app.
        self.path_params: Dict[str, Any] = {}

    # --- helpers ---------------------------------------------------------
    @property
    def query(self) -> MultiDict:
        if self._query is None:
            self._query = parse_query_string(self.query_string)
        return self._query

    @property
    def cookies(self) -> Dict[str, str]:
        if self._cookies is None:
            self._cookies = parse_cookie(self.headers.get("cookie"))
        return self._cookies

    @property
    def content_type(self) -> str:
        return (self.headers.get("content-type") or "").lower()

    @property
    def json(self) -> Any:
        if not isinstance(self._json, _Unset):
            return self._json
        if "application/json" not in self.content_type:
            self._json = None
            return self._json
        try:
            self._json = json.loads(self.body.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self._json = None
        return self._json

    @property
    def form(self) -> MultiDict:
        if self._form is None:
            if "application/x-www-form-urlencoded" in self.content_type:
                self._form = parse_query_string(
                    self.body.decode("utf-8", "replace")
                )
            else:
                self._form = MultiDict()
        return self._form

    def get_header(self, name: str, default: Optional[str] = None) -> Optional[str]:
        return self.headers.get(name, default)

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"<Request {self.method} {self.path}>"
