"""Middleware support.

A middleware is anything that, given a request and a ``call_next`` function,
returns a response. This covers both:

* class-based middlewares subclassing :class:`Middleware` (override
  ``handle``), and
* plain callables ``def mw(request, call_next)``.

The application wraps the route handler with every middleware so they run in
registration order on the way in and in reverse order on the way out.
"""
from __future__ import annotations

from typing import Callable, List

from .request import Request
from .response import Response

# A "next" function takes a Request and returns a Response.
Next = Callable[[Request], Response]
Handler = Callable[[Request], Response]


class Middleware:
    """Base class for class-based middlewares."""

    def handle(self, request: Request, call_next: Next) -> Response:
        # Default pass-through; subclasses override this.
        return call_next(request)

    def __call__(self, request: Request, call_next: Next) -> Response:
        return self.handle(request, call_next)


def _normalize(mw) -> Handler:
    """Accept a Middleware instance or a plain callable.

    ``Middleware`` instances are themselves callable with the
    ``(request, call_next)`` signature, so no special-casing is required.
    """
    if callable(mw):
        return mw
    raise TypeError(f"Middleware must be callable, got {mw!r}")


def build_chain(middlewares: List, final: Handler) -> Handler:
    """Wrap ``final`` with each middleware in registration order.

    ``middlewares[0]`` is the outermost (runs first on the way in).
    """
    chain: Handler = final
    for mw in reversed(middlewares):
        outer = _normalize(mw)
        inner = chain
        chain = lambda req, outer=outer, inner=inner: outer(req, inner)
    return chain
