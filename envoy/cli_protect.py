"""cli_protect.py — CLI subcommands for the env-protect feature."""
from __future__ import annotations
import argparse
from typing import List

from envoy.env_protect import EnvProtector
from envoy.parser import EnvParser


def register_protect_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("protect", help="Check protected-key constraints")
    sub = p.add_subparsers(dest="protect_cmd")

    chk = sub.add_parser("check", help="Check proposed env file against protected keys")
    chk.add_argument("current", help="Current .env file (source of truth for protected keys)")
    chk.add_argument("proposed", help="Proposed .env file to validate")
    chk.add_argument(
        "--protect",
        dest="keys",
        metavar="KEY",
        nargs="+",
        required=True,
        help="Keys to protect",
    )

    lst = sub.add_parser("list", help="List protected keys that exist in an env file")
    lst.add_argument("file", help=".env file to inspect")
    lst.add_argument(
        "--protect",
        dest="keys",
        metavar="KEY",
        nargs="+",
        required=True,
        help="Keys to protect",
    )


def handle_protect_command(args: argparse.Namespace, out=print) -> int:
    if not hasattr(args, "protect_cmd") or args.protect_cmd is None:
        out("Usage: envoy protect <check|list> [options]")
        return 1

    parser = EnvParser()

    if args.protect_cmd == "check":
        try:
            with open(args.current) as fh:
                current_vars = parser.parse(fh.read())
            with open(args.proposed) as fh:
                proposed_vars = parser.parse(fh.read())
        except FileNotFoundError as exc:
            out(f"Error: {exc}")
            return 1

        protector = EnvProtector(args.keys)
        result = protector.check_overwrite(current_vars, proposed_vars)

        if result.is_clean:
            out("OK: no protected-key violations detected.")
            return 0

        for v in result.violations:
            out(f"VIOLATION: {v.key} — {v.reason}")
        return 2

    if args.protect_cmd == "list":
        try:
            with open(args.file) as fh:
                env_vars = parser.parse(fh.read())
        except FileNotFoundError as exc:
            out(f"Error: {exc}")
            return 1

        protector = EnvProtector(args.keys)
        present = [k for k in protector.protected_keys if k in env_vars]
        absent = [k for k in protector.protected_keys if k not in env_vars]

        out(f"Protected keys present ({len(present)}):")
        for k in sorted(present):
            out(f"  {k}")
        if absent:
            out(f"Protected keys absent ({len(absent)}):")
            for k in sorted(absent):
                out(f"  {k}")
        return 0

    out(f"Unknown protect subcommand: {args.protect_cmd}")
    return 1
