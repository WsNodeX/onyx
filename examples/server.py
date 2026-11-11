"""Launcher for the demo application.

Usage:: python examples/server.py [--port 8000] [--host 127.0.0.1]
"""
from __future__ import annotations

import argparse
import os
import sys

# `from examples.demo_app import app` resolves only when the repository root
# is importable, which it is not when this file is run by path from a clone.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from examples.demo_app import app

def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Onyx demo app")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    app.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
