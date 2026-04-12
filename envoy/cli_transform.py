"""CLI subcommands for env-transform."""
from __future__ import annotations

import argparse
from typing import List

from envoy.env_transform import EnvTransformer
from envoy.parser import EnvParser


def register_transform_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("transform", help="Apply value transforms to .env variables")
    sub = p.add_subparsers(dest="transform_cmd")

    run_p = sub.add_parser("run", help="Run a transform on a .env file")
    run_p.add_argument("file", help="Path to .env file")
    run_p.add_argument("transform", help="Transform name (upper, lower, strip, trim_quotes, to_bool)")
    run_p.add_argument("--keys", nargs="+", metavar="KEY", help="Limit to specific keys")
    run_p.add_argument("--in-place", action="store_true", help="Write result back to file")

    list_p = sub.add_parser("list", help="List available transforms")  # noqa: F841


def handle_transform_command(args: argparse.Namespace, out=None) -> int:
    import sys

    if out is None:
        out = sys.stdout

    cmd = getattr(args, "transform_cmd", None)
    if cmd is None:
        out.write("Usage: envoy transform <run|list> [options]\n")
        return 1

    transformer = EnvTransformer()

    if cmd == "list":
        out.write("Available transforms:\n")
        for name in transformer.available():
            out.write(f"  {name}\n")
        return 0

    if cmd == "run":
        import os

        if not os.path.exists(args.file):
            out.write(f"Error: file not found: {args.file}\n")
            return 1

        with open(args.file) as fh:
            raw = fh.read()

        parser = EnvParser()
        vars_ = parser.parse(raw)
        keys = getattr(args, "keys", None)
        result = transformer.transform(vars_, args.transform, keys=keys)

        if result.has_errors:
            for err in result.errors:
                out.write(f"Error: {err}\n")
            return 1

        if not result.has_changes:
            out.write("No changes.\n")
            return 0

        for change in result.changes:
            out.write(f"  {change.key}: {change.original!r} -> {change.transformed!r}\n")

        if getattr(args, "in_place", False):
            serialized = parser.serialize(result.vars)
            with open(args.file, "w") as fh:
                fh.write(serialized)
            out.write(f"Written to {args.file}\n")

        return 0

    out.write(f"Unknown transform subcommand: {cmd}\n")
    return 1
