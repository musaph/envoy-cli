"""CLI subcommands for env-slugify feature."""
from __future__ import annotations

import argparse
from typing import Callable

from envoy.env_slugify import EnvSlugifier
from envoy.parser import EnvParser


def register_slugify_subcommands(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("slugify", help="Normalize variable keys to UPPER_SNAKE_CASE")
    sub = p.add_subparsers(dest="slugify_cmd")

    run_p = sub.add_parser("run", help="Slugify keys in an env file")
    run_p.add_argument("file", help="Path to .env file")
    run_p.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite existing keys on collision",
    )
    run_p.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Preview changes without writing",
    )


def handle_slugify_command(
    args: argparse.Namespace,
    print_fn: Callable[[str], None] = print,
) -> int:
    if not hasattr(args, "slugify_cmd") or args.slugify_cmd is None:
        print_fn("Usage: envoy slugify <subcommand>")
        return 1

    if args.slugify_cmd == "run":
        return _run_slugify(args, print_fn)

    print_fn(f"Unknown subcommand: {args.slugify_cmd}")
    return 1


def _run_slugify(
    args: argparse.Namespace,
    print_fn: Callable[[str], None],
) -> int:
    try:
        with open(args.file, "r") as fh:
            content = fh.read()
    except FileNotFoundError:
        print_fn(f"Error: file not found: {args.file}")
        return 1

    parser = EnvParser()
    slugifier = EnvSlugifier(overwrite=args.overwrite)

    vars_ = parser.parse(content)
    result = slugifier.slugify(vars_)

    if not result.has_changes():
        print_fn("No keys required slugification.")
        return 0

    for change in result.changes:
        print_fn(f"  {change.original_key!r} -> {change.key!r}")

    if result.skipped:
        print_fn(f"Skipped (collision): {', '.join(result.skipped)}")

    if args.dry_run:
        print_fn("Dry-run: no changes written.")
        return 0

    from envoy.parser import EnvParser as _P
    serialized = _P().serialize(result.vars)
    with open(args.file, "w") as fh:
        fh.write(serialized)

    print_fn(f"Slugified {len(result.changes)} key(s).")
    return 0
