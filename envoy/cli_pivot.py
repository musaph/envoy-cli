"""CLI subcommands for env-pivot (swap keys and values)."""
from __future__ import annotations

import argparse
from typing import Callable

from envoy.env_pivot import EnvPivoter
from envoy.parser import EnvParser


def register_pivot_subcommands(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("pivot", help="Swap keys and values in an .env file")
    sub = p.add_subparsers(dest="pivot_cmd")

    run_p = sub.add_parser("run", help="Perform the pivot and print result")
    run_p.add_argument("file", help="Path to .env file")
    run_p.add_argument(
        "--on-collision",
        choices=["skip", "overwrite"],
        default="skip",
        help="Behaviour when pivoted keys collide (default: skip)",
    )
    run_p.add_argument(
        "--include-empty",
        action="store_true",
        help="Include vars with empty values (skipped by default)",
    )


def handle_pivot_command(args: argparse.Namespace, out: Callable[[str], None] = print) -> int:
    if not hasattr(args, "pivot_cmd") or args.pivot_cmd is None:
        out("Usage: envoy pivot <subcommand>  (run)")
        return 1

    if args.pivot_cmd == "run":
        return _run_pivot(args, out)

    out(f"Unknown pivot subcommand: {args.pivot_cmd}")
    return 1


def _run_pivot(args: argparse.Namespace, out: Callable[[str], None]) -> int:
    try:
        with open(args.file) as fh:
            content = fh.read()
    except FileNotFoundError:
        out(f"Error: file not found: {args.file}")
        return 1

    parser = EnvParser()
    vars_ = parser.parse(content)

    pivoter = EnvPivoter(
        skip_empty=not getattr(args, "include_empty", False),
        on_collision=getattr(args, "on_collision", "skip"),
    )
    result = pivoter.pivot(vars_)

    if not result.has_changes:
        out("No pivotable variables found.")
        return 0

    out(f"Pivoted {len(result.changes)} variable(s):")
    for change in result.changes:
        out(f"  {change.original_key}={change.original_value!r}  ->  {change.new_key}={change.new_value!r}")

    if result.collisions:
        out(f"Collisions ({len(result.collisions)}): {', '.join(result.collisions)}")

    if result.skipped:
        out(f"Skipped empty-value keys ({len(result.skipped)}): {', '.join(result.skipped)}")

    return 0
