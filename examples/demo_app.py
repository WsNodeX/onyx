"""A runnable demo application showcasing Onyx features.

Run it with::

    python -m onyx run examples.demo_app:app --port 8000

or simply ``python examples/server.py``.
"""
from __future__ import annotations

from onyx import Blueprint, Onyx, Request, Response, Middleware
from onyx.errors import NotFound, Unauthorized

app = Onyx(name="demo", debug=True)

# In-memory "database" for the demo (resets on restart).
_TODOS: dict = {}
_next_id = [1]


# --- middleware ----------------------------------------------------------
class PoweredByMiddleware(Middleware):
    def handle(self, request: Request, call_next):
        response = call_next(request)
        response.headers.set("X-Powered-By", "Onyx")
        return response


app.add_middleware(PoweredByMiddleware())


# --- custom 404 ----------------------------------------------------------
@app.errorhandler(NotFound)
def handle_not_found(exc: NotFound) -> Response:
    return Response.json(
        {"error": "not_found", "message": exc.detail}, status_code=404
    )


# --- routes --------------------------------------------------------------
@app.get("/")
def index(request: Request) -> Response:
    return Response.html(
        "<h1>Onyx demo</h1>"
        "<p>Try <code>GET /api/todos</code> or <code>POST /api/todos</code>.</p>"
    )


@app.get("/api/todos")
def list_todos(request: Request) -> Response:
    return Response.json(list(_TODOS.values()))


@app.post("/api/todos")
def create_todo(request: Request) -> Response:
    payload = request.json or {}
    title = payload.get("title")
    if not title:
        from onyx.errors import UnprocessableEntity

        raise UnprocessableEntity("Field 'title' is required")
    todo_id = _next_id[0]
    _next_id[0] += 1
    todo = {"id": todo_id, "title": title, "done": bool(payload.get("done", False))}
    _TODOS[todo_id] = todo
    return Response.json(todo, status_code=201)


@app.get("/api/todos/<id:int>")
def get_todo(request: Request) -> Response:
    todo_id = request.path_params["id"]
    todo = _TODOS.get(todo_id)
    if todo is None:
        raise NotFound(f"Todo {todo_id} not found")
    return Response.json(todo)


@app.delete("/api/todos/<id:int>")
def delete_todo(request: Request) -> Response:
    todo_id = request.path_params["id"]
    if todo_id not in _TODOS:
        raise NotFound(f"Todo {todo_id} not found")
    del _TODOS[todo_id]
    return Response.json({"deleted": todo_id})


# --- a small admin blueprint with its own guard --------------------------
admin = Blueprint("admin", url_prefix="/admin")


class AdminGuard(Middleware):
    def handle(self, request: Request, call_next):
        if request.headers.get("X-Admin-Token") != "secret":
            raise Unauthorized("Admin token missing")
        return call_next(request)


admin.use(AdminGuard())


@admin.get("/stats")
def admin_stats(request: Request) -> Response:
    return Response.json({"todos": len(_TODOS), "next_id": _next_id[0]})


app.register_blueprint(admin)
