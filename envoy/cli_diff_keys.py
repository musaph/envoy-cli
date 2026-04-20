"""CLI subcommands for env-diff-keys: compare keys between two .env files."""
from argparse import ArgumentParser, Namespace
from typing import Callable

from envoy.env_diff_keys import EnvDiffKeys
from envoy.parser import EnvParser


def register_diff_keys_subcommands(sub) -> None:
    p: ArgumentParser = sub.add_parser(
        "diff-keys",
        help="Compare keys between two .env files",
    )
    p.add_argument("old", help="Path to the old .env file")
    p.add_argument("new", help="Path to the new .env file")
    p.add_argument(
        "--only-added", action="store_true", help="Show only added keys"
    )
    p.add_argument(
        "--only-removed", action="store_true", help="Show only removed keys"
    )
    p.add_argument(
        "--no-common", action="store_true", help="Hide common keys"
    )


def handle_diff_keys_command(
    args: Namespace, out: Callable[[str], None] = print
) -> int:
    if not hasattr(args, "old"):
        out("Usage: envoy diff-keys <old> <new> [--only-added] [--only-removed] [--no-common]")
        return 1

    parser = EnvParser()
    differ = EnvDiffKeys()

    try:
        with open(args.old) as f:
            old_vars = parser.parse(f.read())
    except FileNotFoundError:
        out(f"Error: file not found: {args.old}")
        return 1

    try:
        with open(args.new) as f:
            new_vars = parser.parse(f.read())
    except FileNotFoundError:
        out(f"Error: file not found: {args.new}")
        return 1

    result = differ.compare(old_vars, new_vars)

    if not result.has_diff and not args.__dict__.get("no_common"):
        if not args.__dict__.get("only_added") and not args.__dict__.get("only_removed"):
            out(f"No key differences found. {len(result.common)} common key(s).")

    for entry in result.entries:
        if entry.status == "added" and not args.__dict__.get("only_removed"):
            out(f"+ {entry.key}")
        elif entry.status == "removed" and not args.__dict__.get("only_added"):
            out(f"- {entry.key}")
        elif entry.status == "common" and not args.__dict__.get("no_common") \
                and not args.__dict__.get("only_added") \
                and not args.__dict__.get("only_removed"):
            out(f"  {entry.key}")

    return 0
