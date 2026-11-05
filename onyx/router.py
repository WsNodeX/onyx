"""URL routing with typed path parameters.

Path patterns support converters, inspired by the common ``<name:type>``
syntax but implemented from scratch:

    /users/<id:int>          -> matches /users/42, captures id="42" as int
    /files/<path:path>       -> matches /files/a/b/c.txt (slashes included)
    /items/<slug>            -> str converter (default)
    /rates/<amount:float>

Converters are: ``str`` (default), ``int``, ``float``, ``path``.
"""
from __future__ import annotations

import re
from typing import Callable, Dict, List, Optional, Tuple

# A handler is any callable accepting a Request and returning a Response
# (or anything the app knows how to wrap). Typed loosely here on purpose.
Handler = Callable


class Route:
    """A single registered route: a pattern, HTTP methods, and a handler."""

    __slots__ = ("pattern", "methods", "handler", "name", "regex", "param_types")

    def __init__(
        self,
        pattern: str,
        methods: List[str],
        handler: Handler,
        name: Optional[str] = None,
    ) -> None:
        self.pattern = pattern
        self.methods = [m.upper() for m in methods]
        self.handler = handler
        self.name = name or handler.__name__
        self.regex, self.param_types = self._compile(pattern)

    @staticmethod
    def _compile(pattern: str) -> Tuple[re.Pattern, Dict[str, str]]:
        param_types: Dict[str, str] = {}
        # Find <name:type> or <name> segments.
        segments: List[str] = []
        pos = 0
        for match in re.finditer(r"<([^>]+)>", pattern):
            # literal text before the param
            if match.start() > pos:
                segments.append(re.escape(pattern[pos : match.start()]))
            spec = match.group(1)
            if ":" in spec:
                name, _, ctype = spec.partition(":")
            else:
                name, ctype = spec, "str"
            param_types[name] = ctype
            if ctype == "int":
                segments.append(r"(?P<%s>\d+)" % name)
            elif ctype == "float":
                segments.append(r"(?P<%s>\d+(?:\.\d+)?)" % name)
            elif ctype == "path":
                segments.append(r"(?P<%s>.+?)" % name)
            else:  # str
                segments.append(r"(?P<%s>[^/]+)" % name)
            pos = match.end()
        if pos < len(pattern):
            segments.append(re.escape(pattern[pos:]))
        regex = re.compile("^" + "".join(segments) + "/?$")
        return regex, param_types

    def match(self, path: str) -> Optional[Dict[str, str]]:
        m = self.regex.match(path)
        if not m:
            return None
        raw = m.groupdict()
        converted: Dict[str, object] = {}
        for key, value in raw.items():
            ctype = self.param_types.get(key, "str")
            if ctype == "int":
                converted[key] = int(value)
            elif ctype == "float":
                converted[key] = float(value)
            else:
                converted[key] = value
        # type: ignore[return-value]
        return converted  # type: ignore[return-value]


class Router:
    """Stores routes and resolves ``(method, path)`` to a handler + params."""

    def __init__(self) -> None:
        self._routes: List[Route] = []
        self._static: Dict[Tuple[str, str], Route] = {}

    def add(
        self,
        pattern: str,
        methods: List[str],
        handler: Handler,
        name: Optional[str] = None,
    ) -> Route:
        # Normalize trailing slash for static equality only.
        route = Route(pattern, methods, handler, name)
        self._routes.append(route)
        return route

    def _methods_for_path(self, path: str) -> List[str]:
        methods: List[str] = []
        for route in self._routes:
            if route.match(path) is not None:
                methods.extend(route.methods)
        # de-dup while keeping order
        seen = set()
        ordered: List[str] = []
        for m in methods:
            if m not in seen:
                seen.add(m)
                ordered.append(m)
        return ordered

    def resolve(self, method: str, path: str) -> Tuple[Handler, Dict[str, object]]:
        """Return ``(handler, params)``.

        Raises:
            NotFound: no route matched the path at all.
            MethodNotAllowed: path matched but method is not permitted.
        """
        from .errors import MethodNotAllowed, NotFound

        method = method.upper()
        allowed: List[str] = []
        for route in self._routes:
            params = route.match(path)
            if params is None:
                continue
            if method in route.methods:
                return route.handler, params
            allowed.extend(route.methods)
        if allowed:
            raise MethodNotAllowed(sorted(set(allowed)))
        raise NotFound(f"No route for {method} {path}")
