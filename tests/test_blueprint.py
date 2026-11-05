import unittest

from onyx import Blueprint, Onyx


class TestBlueprint(unittest.TestCase):
    def test_prefix_join(self):
        bp = Blueprint("api", url_prefix="/api")
        self.assertEqual(bp._join("/users"), "/api/users")
        self.assertEqual(bp._join("/"), "/api")

    def test_register_routes(self):
        bp = Blueprint("api", url_prefix="/api")
        app = Onyx()

        @bp.get("/ping")
        def ping(request):
            return "pong"

        @bp.post("/echo")
        def echo(request):
            return "echo"

        app.register_blueprint(bp)
        client = app.test_client()
        self.assertEqual(client.get("/api/ping").text, "pong")
        self.assertEqual(client.post("/api/echo").text, "echo")

    def test_blueprint_middleware(self):
        bp = Blueprint("admin", url_prefix="/admin")
        app = Onyx()

        from onyx import Middleware

        class Guard(Middleware):
            def handle(self, request, call_next):
                request.guarded = True
                return call_next(request)

        bp.use(Guard())

        @bp.get("/x")
        def x(request):
            return "ok" if getattr(request, "guarded", False) else "no"

        app.register_blueprint(bp)
        client = app.test_client()
        self.assertEqual(client.get("/admin/x").text, "ok")


if __name__ == "__main__":
    unittest.main()
