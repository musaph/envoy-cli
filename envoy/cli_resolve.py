"""CLI subcommands for env-resolve (expand variable references in .env files)."""
from __future__ import annotations

import argparse
from typing import Callable

from envoy.env_resolve import EnvResolver
from envoy.parser import EnvParser


def register_resolve_subcommands(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("resolve", help="Expand $VAR references in a .env file")
    sub = p.add_subparsers(dest="resolve_cmd")

    run_p = sub.add_parser("run", help="Resolve and print expanded variables")
    run_p.add_argument("file", help="Path to .env file")
    run_p.add_argument(
        "--strict",
        action="store_true",
        help="Exit with error if any references remain unresolved",
    )


def handle_resolve_command(
    args: argparse.Namespace,
    print_fn: Callable[[str], None] = print,
) -> int:
    if not hasattr(args, "resolve_cmd") or args.resolve_cmd is None:
        print_fn("Usage: envoy resolve <subcommand>  (run)")
        return 1

    if args.resolve_cmd == "run":
        return _run(args, print_fn)

    print_fn(f"Unknown resolve subcommand: {args.resolve_cmd}")
    return 1


def _run(
    args: argparse.Namespace,
    print_fn: Callable[[str], None],
) -> int:
    import os

    if not os.path.isfile(args.file):
        print_fn(f"Error: file not found: {args.file}")
        return 1

    with open(args.file) as fh:
        raw = fh.read()

    parser = EnvParser()
    vars_ = parser.parse(raw)

    resolver = EnvResolver()
    result = resolver.resolve(vars_)

    for key, value in result.resolved.items():
        print_fn(f"{key}={value}")

    if result.unresolved:
        print_fn(f"\nWarning: unresolved references in: {', '.join(result.unresolved)}")
        if getattr(args, "strict", False):
            return 1

    return 0
