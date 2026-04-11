"""CLI subcommands for placeholder detection."""
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Callable

from envoy.parser import EnvParser
from envoy.env_placeholder import EnvPlaceholderDetector


def register_placeholder_subcommands(sub) -> None:
    p: ArgumentParser = sub.add_parser(
        "placeholder",
        help="Detect unset or placeholder values in a .env file",
    )
    p.add_argument("file", help="Path to the .env file")
    p.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero status if any placeholders are found",
    )


def handle_placeholder_command(
    args: Namespace,
    out: Callable[[str], None] = print,
) -> int:
    if not hasattr(args, "file"):
        out("Usage: envoy placeholder <file> [--strict]")
        return 1

    path = Path(args.file)
    if not path.exists():
        out(f"Error: file not found: {path}")
        return 1

    raw = path.read_text(encoding="utf-8")
    parser = EnvParser()
    vars = parser.parse(raw)

    detector = EnvPlaceholderDetector()
    result = detector.detect(vars)

    out(f"Checked {result.checked} variable(s).")

    if not result.found:
        out("No placeholder values detected.")
        return 0

    out(f"Found {len(result.matches)} placeholder(s):")
    for match in result.matches:
        out(f"  {match.key}={match.value!r}  ({match.reason})")

    return 1 if getattr(args, "strict", False) else 0
