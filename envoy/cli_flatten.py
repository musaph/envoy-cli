"""CLI subcommands for env-flatten feature."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import IO

from envoy.env_flatten import EnvFlattener
from envoy.parser import EnvParser


def register_flatten_subcommands(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "flatten",
        help="Expand JSON-valued vars into dot-notation keys",
    )
    p.add_argument("file", help="Path to .env file")
    p.add_argument(
        "--separator",
        default=".",
        help="Key separator (default: '.')",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing",
    )


def handle_flatten_command(args: argparse.Namespace, out: IO[str] = None) -> int:
    import sys

    out = out or sys.stdout

    if not hasattr(args, "file"):
        out.write("Usage: envoy flatten <file>\n")
        return 1

    path = Path(args.file)
    if not path.exists():
        out.write(f"Error: file not found: {args.file}\n")
        return 1

    parser = EnvParser()
    vars_ = parser.parse(path.read_text())

    separator = getattr(args, "separator", ".")
    flattener = EnvFlattener(separator=separator)
    result = flattener.flatten(vars_)

    if not result.has_changes:
        out.write("No JSON-valued variables found to flatten.\n")
        return 0

    out.write(f"Flattened {len(result.changes)} variable(s):\n")
    for change in result.changes:
        out.write(f"  {change.original_key} -> {change.derived_key}={change.value}\n")

    if result.skipped:
        out.write(f"Skipped {len(result.skipped)} non-JSON variable(s).\n")

    if not getattr(args, "dry_run", False):
        serialized = EnvParser().serialize(result.flattened)
        path.write_text(serialized)
        out.write(f"Written to {args.file}\n")

    return 0
