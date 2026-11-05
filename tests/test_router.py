import unittest

from onyx.errors import MethodNotAllowed, NotFound
from onyx.router import Route, Router


def handler(request):
    return "ok"


class TestRouteCompile(unittest.TestCase):
    def test_static(self):
        r = Route("/health", ["GET"], handler)
        # Trailing slash is treated as equivalent to the bare path.
        self.assertEqual(r.match("/health"), {})
        self.assertEqual(r.match("/health/"), {})

    def test_str_param(self):
        r = Route("/users/<name>", ["GET"], handler)
        self.assertEqual(r.match("/users/alice"), {"name": "alice"})
        self.assertIsNone(r.match("/users/alice/x"))

    def test_int_param(self):
        r = Route("/items/<id:int>", ["GET"], handler)
        self.assertEqual(r.match("/items/42"), {"id": 42})
        self.assertIsNone(r.match("/items/abc"))
        self.assertIsNone(r.match("/items/42/extra"))

    def test_float_param(self):
        r = Route("/r/<v:float>", ["GET"], handler)
        self.assertEqual(r.match("/r/3.14"), {"v": 3.14})
        self.assertEqual(r.match("/r/3"), {"v": 3.0})

    def test_path_param(self):
        r = Route("/files/<p:path>", ["GET"], handler)
        self.assertEqual(r.match("/files/a/b/c.txt"), {"p": "a/b/c.txt"})

    def test_trailing_slash_optional(self):
        r = Route("/api/x", ["GET"], handler)
        self.assertEqual(r.match("/api/x/"), {})

    def test_default_str_converter(self):
        r = Route("/<slug>", ["GET"], handler)
        self.assertEqual(r.match("/hello"), {"slug": "hello"})


class TestRouterResolve(unittest.TestCase):
    def setUp(self):
        self.router = Router()
        self.router.add("/a", ["GET"], handler, "a")
        self.router.add("/b", ["POST"], handler, "b")
        self.router.add("/c/<id:int>", ["GET", "DELETE"], handler, "c")

    def test_resolve_get(self):
        h, params = self.router.resolve("GET", "/a")
        self.assertIs(h, handler)
        self.assertEqual(params, {})

    def test_resolve_param(self):
        h, params = self.router.resolve("GET", "/c/7")
        self.assertEqual(params, {"id": 7})

    def test_method_not_allowed(self):
        with self.assertRaises(MethodNotAllowed) as ctx:
            self.router.resolve("DELETE", "/a")
        self.assertIn("GET", ctx.exception.allowed_methods)

    def test_not_found(self):
        with self.assertRaises(NotFound):
            self.router.resolve("GET", "/nope")

    def test_method_case_insensitive(self):
        h, _ = self.router.resolve("post", "/b")
        self.assertIs(h, handler)


if __name__ == "__main__":
    unittest.main()
