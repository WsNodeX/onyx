import unittest

from onyx.middleware import Middleware, build_chain
from onyx.request import Request
from onyx.response import Response


def final(request):
    return Response("core")


class TaggingMiddleware(Middleware):
    def __init__(self, tag):
        self.tag = tag

    def handle(self, request, call_next):
        request.tag = getattr(request, "tag", "") + self.tag
        resp = call_next(request)
        resp.headers.set("X-Tag", getattr(request, "tag", ""))
        return resp


def function_mw(request, call_next):
    request.fmw = True
    return call_next(request)


class TestMiddlewareChain(unittest.TestCase):
    def test_order_in_and_out(self):
        # outer sets "A", inner sets "B"; request.tag becomes "AB"
        chain = build_chain([TaggingMiddleware("A"), TaggingMiddleware("B")], final)
        req = Request("GET", "/")
        resp = chain(req)
        self.assertEqual(req.tag, "AB")
        self.assertEqual(resp.headers.get("X-Tag"), "AB")
        self.assertEqual(resp.body, b"core")

    def test_function_middleware(self):
        chain = build_chain([function_mw], final)
        req = Request("GET", "/")
        resp = chain(req)
        self.assertTrue(req.fmw)
        self.assertEqual(resp.body, b"core")

    def test_single_middleware(self):
        chain = build_chain([function_mw], final)
        req = Request("GET", "/")
        self.assertEqual(chain(req).body, b"core")

    def test_no_middleware(self):
        chain = build_chain([], final)
        req = Request("GET", "/")
        self.assertEqual(chain(req).body, b"core")


if __name__ == "__main__":
    unittest.main()
