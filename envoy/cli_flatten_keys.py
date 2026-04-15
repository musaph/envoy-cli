"""CLI subcommands for env-key flattening."""
from __future__ import annotations

import argparse
from typing import Callable

from envoy.env_flatten_keys import EnvKeyFlattener
from envoy.parser import EnvParser


def register_flatten_keys_subcommands(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "flatten-keys",
        help="Flatten nested key separators (e.g. APP__DB__HOST -> APP_DB_HOST)",
    )
    p.add_argument("file", help="Path to the .env file")
    p.add_argument(
        "--separator",
        default="__",
        help="Separator to flatten (default: '__')",
    )
    p.add_argument(
        "--replacement",
        default="_",
        help="Replacement string (default: '_')",
    )
    p.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite target key if it already exists",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without writing the file",
    )


def handle_flatten_keys_command(args: argparse.Namespace, out: Callable[[str], None] = print) -> int:
    if not hasattr(args, "file"):
        out("Usage: envoy flatten-keys <file> [options]")
        return 1

    try:
        with open(args.file, "r") as fh:
            content = fh.read()
    except FileNotFoundError:
        out(f"Error: file not found: {args.file}")
        return 1

    parser = EnvParser()
    vars_ = parser.parse(content)

    flattener = EnvKeyFlattener(
        separator=getattr(args, "separator", "__"),
        replacement=getattr(args, "replacement", "_"),
        overwrite=getattr(args, "overwrite", False),
    )
    result = flattener.flatten(vars_)

    if not result.has_changes:
        out("No keys to flatten.")
        return 0

    for change in result.changes:
        out(f"  {change.original} -> {change.flattened}")
    for key in result.skipped:
        out(f"  SKIP (conflict): {key}")

    if not getattr(args, "dry_run", False):
        new_content = parser.serialize(result.vars)
        with open(args.file, "w") as fh:
            fh.write(new_content)
        out(f"Written {len(result.changes)} change(s) to {args.file}")
    else:
        out("Dry-run: no changes written.")

    return 0
