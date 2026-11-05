"""Blueprints let you group routes under a common URL prefix and register
them on an application in one call. This keeps larger projects organised
without forcing a single giant file of decorators.
"""
from __future__ import annotations

from typing import Callable, List, Optional, Tuple

from .middleware import build_chain


class Blueprint:
    """A collection of routes (and optional middleware) with a URL prefix."""

    def __init__(self, name: str, url_prefix: str = "") -> None:
        self.name = name
        self.url_prefix = url_prefix.rstrip("/")
        self._deferred: List[Tuple[str, List[str], Callable, Optional[str]]] = []
        self._middlewares: List = []

    def _join(self, pattern: str) -> str:
        if not self.url_prefix:
            return pattern
        if not pattern or pattern == "/":
            return self.url_prefix or "/"
        return self.url_prefix + pattern

    def route(self, pattern: str, methods: Optional[List[str]] = None, name: Optional[str] = None):
        methods = methods or ["GET"]

        def decorator(handler: Callable) -> Callable:
            self._deferred.append((self._join(pattern), methods, handler, name))
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

    def use(self, middleware) -> None:
        self._middlewares.append(middleware)

    def _wrap(self, handler: Callable) -> Callable:
        """Wrap a handler with this blueprint's own middlewares only."""
        if not self._middlewares:
            return handler
        wrapped = build_chain(self._middlewares, lambda req: handler(req))
        wrapped.__name__ = getattr(handler, "__name__", "handler")
        return wrapped

    def register_on(self, app) -> None:
        for pattern, methods, handler, name in self._deferred:
            wrapped = self._wrap(handler)
            app.route(pattern, methods=methods, name=name)(wrapped)
