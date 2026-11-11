"""Compatibility launcher for Glyphform.

Run with ``python glyphform.py`` or ``python -m glyphform``.
"""
from glyphform.main import run

if __name__ == "__main__":
    import sys
    if not sys.stdout.isatty():
        sys.stderr.write("Run this in an interactive terminal.\n")
        raise SystemExit(1)
    run()
