"""cli_cloak.py — CLI subcommands for env-cloak feature."""
from __future__ import annotations
import argparse
from typing import Callable

from envoy.env_cloak import EnvCloaker
from envoy.parser import EnvParser


def register_cloak_subcommands(sub: argparse.ArgumentParser) -> None:
    sub.add_argument("file", help="Path to .env file")
    sub.add_argument(
        "--pattern",
        dest="patterns",
        action="append",
        default=[],
        metavar="PATTERN",
        help="Key pattern to cloak (repeatable, case-insensitive regex)",
    )
    sub.add_argument(
        "--symbol",
        default="<cloaked>",
        help="Replacement symbol (default: <cloaked>)",
    )


def handle_cloak_command(args: argparse.Namespace, print_fn: Callable = print) -> int:
    if not hasattr(args, "file"):
        print_fn("Usage: envoy cloak <file> [--pattern PATTERN ...]")
        return 1

    import os

    if not os.path.isfile(args.file):
        print_fn(f"Error: file not found: {args.file}")
        return 1

    patterns = args.patterns or []
    if not patterns:
        print_fn("Error: at least one --pattern is required")
        return 1

    with open(args.file) as fh:
        raw = fh.read()

    parser = EnvParser()
    vars_ = parser.parse(raw)

    cloaker = EnvCloaker(patterns=patterns, symbol=args.symbol)
    result = cloaker.cloak(vars_)

    if not result.has_changes:
        print_fn("No variables matched the given patterns.")
        return 0

    print_fn(f"Cloaked {len(result.changes)} variable(s):")
    for change in result.changes:
        print_fn(f"  {change.key}: {change.original!r} -> {change.cloaked!r}")

    return 0
