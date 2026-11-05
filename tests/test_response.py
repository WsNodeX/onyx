import unittest

from onyx.response import Response


class TestResponse(unittest.TestCase):
    def test_text_default(self):
        r = Response.text("hello")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.body, b"hello")
        self.assertIn("text/plain", r.headers.get("content-type"))

    def test_json(self):
        r = Response.json({"a": 1})
        self.assertEqual(r.body, b'{"a": 1}')
        self.assertIn("application/json", r.headers.get("content-type"))

    def test_html(self):
        r = Response.html("<p>x</p>")
        self.assertIn("text/html", r.headers.get("content-type"))

    def test_redirect(self):
        r = Response.redirect("/login", status_code=302)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.headers.get("location"), "/login")

    def test_status_line(self):
        r = Response("x", 404)
        self.assertEqual(r.status_line, "404 Not Found")

    def test_set_cookie(self):
        r = Response("x")
        r.set_cookie("sid", "abc", max_age=3600, httponly=True)
        self.assertIn("sid=abc", r.header_list()[-1][1])
        self.assertIn("HttpOnly", r.header_list()[-1][1])

    def test_delete_cookie(self):
        r = Response("x")
        r.delete_cookie("sid")
        cookie = r.header_list()[-1][1]
        self.assertIn("sid=", cookie)
        self.assertIn("Max-Age=0", cookie)

    def test_bytes_body(self):
        r = Response(b"\x00\x01", content_type="application/octet-stream")
        self.assertEqual(r.body, b"\x00\x01")

    def test_data_property(self):
        r = Response.text("hi")
        self.assertEqual(r.data, b"hi")


if __name__ == "__main__":
    unittest.main()
