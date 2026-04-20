"""CLI subcommands for env-swap feature."""
from __future__ import annotations

import argparse
from typing import Callable

from envoy.env_swap import EnvSwapper
from envoy.parser import EnvParser


def register_swap_subcommands(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("swap", help="Swap keys and values in an env file")
    sub = p.add_subparsers(dest="swap_cmd")

    run_p = sub.add_parser("run", help="Perform the swap")
    run_p.add_argument("file", help="Path to .env file")
    run_p.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite colliding keys",
    )
    run_p.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Preview changes without writing",
    )


def handle_swap_command(args: argparse.Namespace, out: Callable[[str], None] = print) -> int:
    swap_cmd = getattr(args, "swap_cmd", None)
    if swap_cmd is None:
        out("Usage: envoy swap <subcommand>  [run]")
        return 1

    if swap_cmd == "run":
        return _run_swap(args, out)

    out(f"Unknown swap subcommand: {swap_cmd}")
    return 1


def _run_swap(args: argparse.Namespace, out: Callable[[str], None]) -> int:
    try:
        content = open(args.file).read()
    except FileNotFoundError:
        out(f"Error: file not found: {args.file}")
        return 2

    parser = EnvParser()
    vars_ = parser.parse(content)
    swapper = EnvSwapper(overwrite=getattr(args, "overwrite", False))
    result = swapper.swap(vars_)

    if not result.has_changes:
        out("No swappable pairs found.")
        return 0

    for change in result.changes:
        out(f"  {change.original_key}={change.original_value} -> {change.new_key}={change.new_value}")

    if result.skipped:
        out(f"Skipped {len(result.skipped)} key(s): {', '.join(result.skipped)}")

    if getattr(args, "dry_run", False):
        out("Dry run — no changes written.")
        return 0

    serialized = EnvParser.serialize(result.vars)
    with open(args.file, "w") as f:
        f.write(serialized)

    out(f"Swapped {len(result.changes)} pair(s) in {args.file}")
    return 0
