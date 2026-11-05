import json
import unittest

from onyx.errors import (
    BadRequest,
    Forbidden,
    HTTPError,
    MethodNotAllowed,
    NotFound,
    Unauthorized,
    UnprocessableEntity,
    from_status,
)


class TestErrors(unittest.TestCase):
    def test_status_codes(self):
        self.assertEqual(BadRequest().status_code, 400)
        self.assertEqual(Unauthorized().status_code, 401)
        self.assertEqual(Forbidden().status_code, 403)
        self.assertEqual(NotFound().status_code, 404)
        self.assertEqual(UnprocessableEntity().status_code, 422)

    def test_custom_detail(self):
        e = NotFound("missing thing")
        self.assertEqual(e.detail, "missing thing")
        self.assertEqual(e.status_code, 404)

    def test_body_is_json(self):
        e = NotFound("x")
        payload = json.loads(e.as_response_body().decode())
        self.assertEqual(payload["error"], "NotFound")
        self.assertEqual(payload["detail"], "x")

    def test_method_not_allowed_allowed_list(self):
        e = MethodNotAllowed(["GET", "POST"])
        self.assertEqual(sorted(e.allowed_methods), ["GET", "POST"])
        payload = json.loads(e.as_response_body().decode())
        self.assertIn("GET", payload["allowed"])

    def test_from_status(self):
        self.assertIsInstance(from_status(404), NotFound)
        self.assertIsInstance(from_status(401), Unauthorized)
        self.assertIsInstance(from_status(500), HTTPError)

    def test_is_http_error(self):
        self.assertIsInstance(NotFound(), HTTPError)


if __name__ == "__main__":
    unittest.main()
