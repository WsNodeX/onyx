#!/usr/bin/env python3
"""
In-process coverage for the demo application.

The demo app is what the README points at and what the web console tests exercise
through HTTP, but nothing drove it directly: the existing suite covered the
framework's router, middleware and errors, and one CLI test checked that a bad
module path fails. So a change to examples/demo_app.py could break every route
without turning anything red.

TestClient runs the app without a socket, which is what makes this cheap enough
to keep in the default suite.
"""
from __future__ import annotations

import unittest

from onyx import Onyx

from examples.demo_app import _TODOS, app


class DemoAppTest(unittest.TestCase):
    def setUp(self) -> None:
        # The app keeps its state in a module-level dict; each test starts clean
        # so ordering cannot matter.
        _TODOS.clear()
        self.client = app.test_client()

    def test_index_renders(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("Onyx demo", r.text)

    def test_list_starts_empty(self):
        r = self.client.get("/api/todos")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), [])

    def test_create_then_read(self):
        created = self.client.post("/api/todos", json={"title": "buy milk"})
        self.assertEqual(created.status_code, 201)
        todo = created.json()
        self.assertEqual(todo["title"], "buy milk")
        self.assertFalse(todo["done"])

        fetched = self.client.get(f"/api/todos/{todo['id']}")
        self.assertEqual(fetched.status_code, 200)
        self.assertEqual(fetched.json()["id"], todo["id"])

    def test_list_reflects_creation(self):
        self.client.post("/api/todos", json={"title": "one"})
        self.client.post("/api/todos", json={"title": "two"})
        r = self.client.get("/api/todos")
        self.assertEqual([t["title"] for t in r.json()], ["one", "two"])

    def test_create_without_title_is_rejected(self):
        r = self.client.post("/api/todos", json={})
        # The handler raises UnprocessableEntity, which the framework maps to 422.
        self.assertEqual(r.status_code, 422)

    def test_delete_then_missing(self):
        created = self.client.post("/api/todos", json={"title": "temp"}).json()
        deleted = self.client.delete(f"/api/todos/{created['id']}")
        self.assertIn(deleted.status_code, (200, 204))
        gone = self.client.get(f"/api/todos/{created['id']}")
        self.assertEqual(gone.status_code, 404)

    def test_unknown_path_uses_error_handler(self):
        r = self.client.get("/no-such-route")
        self.assertEqual(r.status_code, 404)
        # The demo registers an errorhandler for NotFound; its shape proves the
        # handler ran rather than the framework's default page.
        self.assertIsInstance(r.json(), dict)

    def test_admin_requires_token(self):
        r = self.client.get("/admin/stats")
        self.assertEqual(r.status_code, 401)

    def test_admin_with_token(self):
        r = self.client.get("/admin/stats", headers={"X-Admin-Token": "secret"})
        self.assertEqual(r.status_code, 200)
        self.assertIn("todos", r.json())


if __name__ == "__main__":
    unittest.main(verbosity=2)
