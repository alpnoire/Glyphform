"""Run Glyphform with python -m glyphform."""

import argparse
import sys

from .main import run


def main():
    parser = argparse.ArgumentParser(
        description="Glyphform: Terminal Particle Animation Engine"
    )

    parser.add_argument(
        "--text",
        type=str,
        help="Display custom animated particle text.",
    )

    args = parser.parse_args()

    if args.text is not None and not args.text.strip():
        parser.error("Text cannot be empty.")

    if not sys.stdout.isatty():
        sys.stderr.write("Run this in an interactive terminal.\n")
        raise SystemExit(1)

    run(text=args.text)


if __name__ == "__main__":
    main()