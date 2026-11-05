import threading
import time
import unittest
import urllib.request

from onyx import Onyx, Response
from onyx.server import make_server


class TestDevServer(unittest.TestCase):
    def setUp(self):
        app = Onyx(name="srv")

        @app.get("/")
        def index(request):
            return Response.text("hello-server")

        @app.get("/json")
        def j(request):
            return {"ok": True}

        @app.post("/echo")
        def echo(request):
            return Response.json(request.json, status_code=201)

        self.server = make_server(app, host="127.0.0.1", port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        # Give the socket a moment and discover the assigned port.
        for _ in range(50):
            if self.server.server_address[1] != 0:
                break
            time.sleep(0.01)
        self.port = self.server.server_address[1]

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def _url(self, path):
        return f"http://127.0.0.1:{self.port}{path}"

    def test_get(self):
        with urllib.request.urlopen(self._url("/"), timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            self.assertEqual(resp.read().decode(), "hello-server")

    def test_json(self):
        with urllib.request.urlopen(self._url("/json"), timeout=5) as resp:
            body = resp.read().decode()
            self.assertIn('"ok": true', body)

    def test_post(self):
        data = '{"a":1}'.encode()
        req = urllib.request.Request(
            self._url("/echo"),
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 201)
            self.assertEqual(resp.read().decode(), '{"a": 1}')


if __name__ == "__main__":
    unittest.main()
