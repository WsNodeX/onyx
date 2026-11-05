"""Command-line entrypoint: ``python -m onyx run module:app``.

Lets you launch an application without writing a ``if __name__ == '__main__'``
boilerplate block, which is handy for quick demos and container starts.
"""
from __future__ import annotations

import argparse
import importlib
import sys


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="onyx", description="Onyx web framework CLI")
    sub = parser.add_subparsers(dest="command")

    run_parser = sub.add_parser("run", help="Serve an application")
    run_parser.add_argument(
        "target", help="Import target in 'module:app' form (app defaults to 'app')."
    )
    run_parser.add_argument("--host", default="127.0.0.1", help="Bind host.")
    run_parser.add_argument("--port", type=int, default=8000, help="Bind port.")

    args = parser.parse_args(argv)

    if args.command != "run":
        parser.print_help()
        return 1

    module_name, _, attr = args.target.partition(":")
    if not attr:
        attr = "app"
    try:
        module = importlib.import_module(module_name)
        app = getattr(module, attr)
    except (ImportError, AttributeError) as exc:
        print(f"onyx: could not load '{args.target}': {exc}", file=sys.stderr)
        return 2

    app.run(host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
