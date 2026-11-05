import unittest

from onyx.datastructures import Headers
from onyx.request import Request


def make_request(**kw):
    headers = kw.pop("headers", Headers())
    return Request("GET", "/", headers=headers, **kw)


class TestRequestParsing(unittest.TestCase):
    def test_query(self):
        req = make_request(query_string="q=onyx&page=2&q=orm")
        self.assertEqual(req.query.get("q"), "onyx")
        self.assertEqual(req.query.getlist("q"), ["onyx", "orm"])
        self.assertEqual(req.query.get("page"), "2")

    def test_json(self):
        body = b'{"name": "onyx", "n": 3}'
        headers = Headers([("Content-Type", "application/json")])
        req = Request("POST", "/", headers=headers, body=body)
        self.assertEqual(req.json["name"], "onyx")
        self.assertEqual(req.json["n"], 3)

    def test_json_invalid_returns_none(self):
        headers = Headers([("Content-Type", "application/json")])
        req = Request("POST", "/", headers=headers, body=b"{bad")
        self.assertIsNone(req.json)

    def test_json_not_json_content_type(self):
        req = make_request(body=b'{"a":1}')
        self.assertIsNone(req.json)

    def test_form(self):
        body = b"title=hi&done=1"
        headers = Headers(
            [("Content-Type", "application/x-www-form-urlencoded")]
        )
        req = Request("POST", "/", headers=headers, body=body)
        self.assertEqual(req.form.get("title"), "hi")
        self.assertEqual(req.form.get("done"), "1")

    def test_cookies(self):
        headers = Headers([("Cookie", "sid=abc; theme=dark")])
        req = make_request(headers=headers)
        self.assertEqual(req.cookies["sid"], "abc")
        self.assertEqual(req.cookies["theme"], "dark")

    def test_method_upper(self):
        req = make_request()
        # constructor already upper-cases
        self.assertEqual(req.method, "GET")


if __name__ == "__main__":
    unittest.main()
