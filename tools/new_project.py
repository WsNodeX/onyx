"""Scaffold a new Onyx project from the command line.

Usage::

    python tools/new_project.py my_service

Creates ``my_service/app.py`` (a minimal Onyx app) and an empty
``my_service/requirements.txt`` so you can start coding immediately.
"""
from __future__ import annotations

import os
import sys


_TEMPLATE = '''from onyx import Onyx, Response

app = Onyx(name="{name}")


@app.get("/")
def index(request):
    return Response.json({{"service": "{name}", "status": "ok"}})


@app.get("/health")
def health(request):
    return Response.text("ok", status_code=200)


if __name__ == "__main__":
    app.run(port=8000)
'''


def scaffold(target_dir: str, name: str) -> None:
    os.makedirs(target_dir, exist_ok=True)
    with open(os.path.join(target_dir, "app.py"), "w", encoding="utf-8") as fh:
        fh.write(_TEMPLATE.format(name=name))
    with open(
        os.path.join(target_dir, "requirements.txt"), "w", encoding="utf-8"
    ) as fh:
        fh.write("# Onyx has zero runtime dependencies.\n")
    print(f"Created a new Onyx project in ./{target_dir}")


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python tools/new_project.py <project_name>", file=sys.stderr)
        return 1
    name = sys.argv[1]
    scaffold(name, name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
