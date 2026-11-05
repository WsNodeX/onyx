import unittest

from onyx.datastructures import (
    Headers,
    MultiDict,
    build_set_cookie,
    parse_cookie,
    parse_query_string,
)


class TestHeaders(unittest.TestCase):
    def test_case_insensitive_get(self):
        h = Headers([("Content-Type", "text/plain")])
        self.assertEqual(h.get("content-type"), "text/plain")
        self.assertEqual(h.get("CONTENT-TYPE"), "text/plain")

    def test_add_keeps_multiple(self):
        h = Headers()
        h.add("X-Tag", "a")
        h.add("X-Tag", "b")
        self.assertEqual(h.getlist("x-tag"), ["a", "b"])

    def test_set_replaces(self):
        h = Headers([("Accept", "x")])
        h.set("accept", "y")
        self.assertEqual(h.getlist("accept"), ["y"])

    def test_contains(self):
        h = Headers([("X-A", "1")])
        self.assertIn("x-a", h)
        self.assertNotIn("x-b", h)


class TestMultiDict(unittest.TestCase):
    def test_getlist_and_first_wins(self):
        md = MultiDict([("a", "1"), ("a", "2"), ("b", "3")])
        self.assertEqual(md.getlist("a"), ["1", "2"])
        self.assertEqual(md.get("a"), "1")
        self.assertEqual(md.get("b"), "3")
        self.assertIsNone(md.get("missing"))

    def test_keys(self):
        md = MultiDict([("x", "1"), ("y", "2")])
        self.assertEqual(sorted(md.keys()), ["x", "y"])


class TestParseQueryString(unittest.TestCase):
    def test_simple(self):
        md = parse_query_string("a=1&b=2&a=3")
        self.assertEqual(md.getlist("a"), ["1", "3"])
        self.assertEqual(md.get("b"), "2")

    def test_blank_values_kept(self):
        md = parse_query_string("q=&x=1")
        self.assertEqual(md.get("q"), "")
        self.assertEqual(md.get("x"), "1")

    def test_empty(self):
        md = parse_query_string("")
        self.assertEqual(md.keys(), [])


class TestCookies(unittest.TestCase):
    def test_parse(self):
        c = parse_cookie("session=abc; theme=dark")
        self.assertEqual(c, {"session": "abc", "theme": "dark"})

    def test_parse_empty(self):
        self.assertEqual(parse_cookie(None), {})
        self.assertEqual(parse_cookie(""), {})

    def test_parse_quoted(self):
        c = parse_cookie('token="a b"')
        self.assertEqual(c.get("token"), "a b")

    def test_build_set_cookie_basic(self):
        header = build_set_cookie("sid", "xyz", path="/")
        self.assertIn("sid=xyz", header)
        self.assertIn("Path=/", header)

    def test_build_set_cookie_max_age(self):
        header = build_set_cookie("sid", "xyz", max_age=3600)
        self.assertIn("Max-Age=3600", header)
        self.assertIn("Expires=", header)

    def test_build_set_cookie_flags(self):
        header = build_set_cookie(
            "sid", "xyz", secure=True, httponly=True, samesite="Lax"
        )
        self.assertIn("Secure", header)
        self.assertIn("HttpOnly", header)
        self.assertIn("SameSite=Lax", header)


if __name__ == "__main__":
    unittest.main()
