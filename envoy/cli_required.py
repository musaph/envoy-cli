"""CLI subcommands for checking required environment variables."""
from typing import List

from envoy.env_required import EnvRequiredChecker
from envoy.parser import EnvParser


def register_required_subcommands(subparsers) -> None:
    p = subparsers.add_parser("required", help="Check required env vars")
    sub = p.add_subparsers(dest="required_cmd")

    chk = sub.add_parser("check", help="Verify required keys exist in a file")
    chk.add_argument("file", help="Path to .env file")
    chk.add_argument(
        "keys",
        nargs="+",
        help="Required key names",
    )
    chk.add_argument(
        "--allow-empty",
        action="store_true",
        default=False,
        help="Allow keys with empty values",
    )


def handle_required_command(args, out=None) -> int:
    import sys

    out = out or sys.stdout

    if not hasattr(args, "required_cmd") or args.required_cmd is None:
        out.write("Usage: envoy required <check>\n")
        return 1

    if args.required_cmd == "check":
        return _run_check(args, out)

    out.write(f"Unknown required subcommand: {args.required_cmd}\n")
    return 1


def _run_check(args, out) -> int:
    import os

    if not os.path.isfile(args.file):
        out.write(f"Error: file not found: {args.file}\n")
        return 1

    with open(args.file) as fh:
        raw = fh.read()

    parser = EnvParser()
    vars_ = parser.parse(raw)

    allow_empty: bool = getattr(args, "allow_empty", False)
    checker = EnvRequiredChecker(required_keys=args.keys, allow_empty=allow_empty)
    result = checker.check(vars_)

    if result.is_satisfied:
        out.write(f"All {len(args.keys)} required key(s) satisfied.\n")
        return 0

    for v in result.missing:
        out.write(f"MISSING  {v.key}: {v.reason}\n")
    for v in result.empty:
        out.write(f"EMPTY    {v.key}: {v.reason}\n")

    out.write(
        f"\n{len(result.violations)} violation(s) found.\n"
    )
    return 1
