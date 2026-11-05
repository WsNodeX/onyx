"""Reusable container types: case-insensitive headers, multi-value dicts,
and RFC-compliant cookie (de)serialization.

These are deliberately dependency-free and small; they cover the 95% of cases
a web framework actually needs without pulling in ``multidict``.
"""
from __future__ import annotations

from collections import OrderedDict
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import parse_qsl


def _normalize(name: str) -> str:
    return name.lower()


class Headers:
    """A case-insensitive, multi-value mapping of HTTP header names to values."""

    def __init__(self, items: Optional[Iterable[Tuple[str, str]]] = None) -> None:
        # Preserve insertion order but key lookups ignore case.
        self._store: "OrderedDict[str, List[str]]" = OrderedDict()
        if items:
            for key, value in items:
                self.add(key, value)

    def add(self, key: str, value: str) -> None:
        norm = _normalize(key)
        self._store.setdefault(norm, []).append(value)

    def set(self, key: str, value: str) -> None:
        norm = _normalize(key)
        self._store[norm] = [value]

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        norm = _normalize(key)
        values = self._store.get(norm)
        return values[-1] if values else default

    def getlist(self, key: str) -> List[str]:
        norm = _normalize(key)
        return list(self._store.get(norm, []))

    def __contains__(self, key: str) -> bool:
        return _normalize(key) in self._store

    def __iter__(self):
        for norm, values in self._store.items():
            for value in values:
                yield norm, value

    def items(self):
        return list(self.__iter__())

    def to_wsgi_list(self) -> List[Tuple[str, str]]:
        return [(k, v) for k, v in self.__iter__()]


class MultiDict:
    """A mapping that may hold several values for the same key (query / form)."""

    def __init__(self, items: Optional[Iterable[Tuple[str, str]]] = None) -> None:
        self._store: "OrderedDict[str, List[str]]" = OrderedDict()
        if items:
            for key, value in items:
                self.add(key, value)

    def add(self, key: str, value: str) -> None:
        self._store.setdefault(key, []).append(value)

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        values = self._store.get(key)
        return values[0] if values else default

    def getlist(self, key: str) -> List[str]:
        return list(self._store.get(key, []))

    def keys(self):
        return list(self._store.keys())

    def __contains__(self, key: str) -> bool:
        return key in self._store

    def __iter__(self):
        for key, values in self._store.items():
            for value in values:
                yield key, value

    def items(self):
        return list(self.__iter__())


def parse_query_string(qs: str) -> MultiDict:
    """Parse a raw query string into a :class:`MultiDict`."""
    return MultiDict(parse_qsl(qs, keep_blank_values=True))


_COOKIE_SEP = ";"


def parse_cookie(header_value: Optional[str]) -> Dict[str, str]:
    """Turn a ``Cookie`` header value into a plain dict."""
    cookies: Dict[str, str] = {}
    if not header_value:
        return cookies
    for part in header_value.split(_COOKIE_SEP):
        part = part.strip()
        if not part or "=" not in part:
            continue
        name, _, value = part.partition("=")
        name = name.strip()
        value = value.strip().strip('"')
        if name:
            cookies[name] = value
    return cookies


def _quote_cookie_value(value: str) -> str:
    # Only wrap in quotes when the value contains characters that need it.
    if any(ch in value for ch in '";, \\'):
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return value


def build_set_cookie(
    name: str,
    value: str,
    *,
    max_age: Optional[int] = None,
    path: str = "/",
    domain: Optional[str] = None,
    secure: bool = False,
    httponly: bool = False,
    samesite: Optional[str] = None,
) -> str:
    """Serialize a ``Set-Cookie`` header value (single cookie)."""
    parts = [f"{name}={_quote_cookie_value(value)}"]
    if max_age is not None:
        parts.append(f"Max-Age={int(max_age)}")
        # Expires is derived from Max-Age for broader client support.
        import time

        expires = time.gmtime(time.time() + int(max_age))
        stamp = time.strftime("%a, %d %b %Y %H:%M:%S GMT", expires)
        parts.append(f"Expires={stamp}")
    if domain:
        parts.append(f"Domain={domain}")
    if path:
        parts.append(f"Path={path}")
    if secure:
        parts.append("Secure")
    if httponly:
        parts.append("HttpOnly")
    if samesite:
        parts.append(f"SameSite={samesite}")
    return "; ".join(parts)
