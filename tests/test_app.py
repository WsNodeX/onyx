import unittest

from onyx import Middleware, Onyx, Request, Response
from onyx.errors import NotFound, Unauthorized, UnprocessableEntity


def build_app():
    app = Onyx(name="test")

    @app.get("/")
    def root(request):
        return Response.text("home")

    @app.get("/json")
    def j(request):
        return {"hello": "world"}

    @app.get("/users/<id:int>")
    def user(request):
        return {"id": request.path_params["id"]}

    @app.post("/echo")
    def echo(request):
        return Response.json(request.json, status_code=201)

    @app.put("/items/<id:int>")
    def put_item(request):
        return {"updated": request.path_params["id"]}

    @app.delete("/items/<id:int>")
    def del_item(request):
        return Response.text("deleted", 204)

    @app.get("/tuple")
    def tup(request):
        return ("custom", 418, {"X-Custom": "yes"})

    @app.get("/bytes")
    def by(request):
        return b"\x01binary"

    @app.get("/none")
    def none(request):
        return None

    @app.get("/boom")
    def boom(request):
        raise ValueError("kaboom")

    @app.errorhandler(NotFound)
    def not_found(exc):
        return Response.json({"message": exc.detail}, status_code=404)

    class HeaderMW(Middleware):
        def handle(self, request, call_next):
            resp = call_next(request)
            resp.headers.set("X-Test", "1")
            return resp

    app.add_middleware(HeaderMW())
    return app


class TestAppIntegration(unittest.TestCase):
    def setUp(self):
        self.client = build_app().test_client()

    def test_get_text(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.text, "home")

    def test_get_json(self):
        r = self.client.get("/json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"hello": "world"})
        self.assertIn("application/json", r.headers.get("content-type"))

    def test_path_param_int(self):
        r = self.client.get("/users/99")
        self.assertEqual(r.json(), {"id": 99})

    def test_path_param_not_int(self):
        r = self.client.get("/users/abc")
        self.assertEqual(r.status_code, 404)

    def test_post_json(self):
        r = self.client.post("/echo", json={"a": 1})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json(), {"a": 1})

    def test_put(self):
        r = self.client.put("/items/5")
        self.assertEqual(r.json(), {"updated": 5})

    def test_delete(self):
        r = self.client.delete("/items/5")
        self.assertEqual(r.status_code, 204)

    def test_404_custom_handler(self):
        r = self.client.get("/missing")
        self.assertEqual(r.status_code, 404)
        self.assertIn("message", r.json())

    def test_405_allow_header(self):
        r = self.client.post("/")  # only GET registered
        self.assertEqual(r.status_code, 405)
        self.assertIn("GET", r.headers.get("allow"))

    def test_tuple_response(self):
        r = self.client.get("/tuple")
        self.assertEqual(r.status_code, 418)
        self.assertEqual(r.text, "custom")
        self.assertEqual(r.headers.get("X-Custom"), "yes")

    def test_bytes_response(self):
        r = self.client.get("/bytes")
        self.assertEqual(r.content, b"\x01binary")

    def test_none_response_is_500(self):
        r = self.client.get("/none")
        self.assertEqual(r.status_code, 500)

    def test_unhandled_exception_is_500(self):
        r = self.client.get("/boom")
        self.assertEqual(r.status_code, 500)

    def test_middleware_header(self):
        r = self.client.get("/")
        self.assertEqual(r.headers.get("X-Test"), "1")

    def test_query_roundtrip(self):
        r = self.client.get("/json?x=1")
        # query accessible through request in handler; just ensure 200
        self.assertEqual(r.status_code, 200)

    def test_cookie_set(self):
        app = Onyx()

        @app.get("/set")
        def set_cookie(request):
            resp = Response.text("ok")
            resp.set_cookie("sid", "abc", httponly=True)
            return resp

        r = app.test_client().get("/set")
        self.assertEqual(r.cookies.get("sid"), "abc")

    def test_request_cookies(self):
        app = Onyx()

        @app.get("/who")
        def who(request):
            return Response.text(request.cookies.get("sid", ""))

        r = app.test_client().get("/who", cookies={"sid": "xyz"})
        self.assertEqual(r.text, "xyz")

    def test_error_handler_for_specific_exception(self):
        app = Onyx()

        @app.get("/no")
        def no(request):
            raise Unauthorized("no token")

        @app.errorhandler(Unauthorized)
        def handle(exc):
            return Response.json({"err": exc.detail}, status_code=401)

        r = app.test_client().get("/no")
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.json()["err"], "no token")

    def test_validation_error(self):
        app = Onyx()

        @app.post("/v")
        def v(request):
            if not request.json:
                raise UnprocessableEntity("bad")
            return Response.text("ok")

        r = app.test_client().post("/v", json=None)
        self.assertEqual(r.status_code, 422)


if __name__ == "__main__":
    unittest.main()
