import argparse
from typing import Callable

from envoy.env_whitelist import EnvWhitelist
from envoy.parser import EnvParser


def register_whitelist_subcommands(sub: argparse.ArgumentParser) -> None:
    sub.add_argument("file", help="Path to the .env file")
    sub.add_argument(
        "--allow",
        dest="allowed_keys",
        metavar="KEY",
        nargs="+",
        required=True,
        help="Keys that are permitted",
    )
    sub.add_argument(
        "--strict",
        action="store_true",
        default=True,
        help="Report violations for keys not in the whitelist (default: on)",
    )
    sub.add_argument(
        "--filter",
        dest="filter_only",
        action="store_true",
        help="Output only allowed vars instead of reporting violations",
    )


def handle_whitelist_command(args: object, out: Callable[[str], None] = print) -> int:
    if not hasattr(args, "file"):
        out("Usage: envoy whitelist <file> --allow KEY [KEY ...]")
        return 1

    try:
        raw = open(args.file).read()  # type: ignore[attr-defined]
    except FileNotFoundError:
        out(f"Error: file not found: {args.file}")  # type: ignore[attr-defined]
        return 1

    parser = EnvParser()
    vars_ = parser.parse(raw)
    whitelist = EnvWhitelist(
        allowed_keys=args.allowed_keys,  # type: ignore[attr-defined]
        strict=getattr(args, "strict", True),
    )

    if getattr(args, "filter_only", False):
        filtered = whitelist.filter(vars_)
        out(f"Filtered to {len(filtered)} allowed key(s):")
        for k, v in filtered.items():
            out(f"  {k}={v}")
        return 0

    result = whitelist.check(vars_)
    out(f"Allowed: {len(result.allowed)}  Violations: {len(result.violations)}")
    for v in result.violations:
        out(f"  [VIOLATION] {v.key}: {v.reason}")
    return 0 if result.is_clean else 1
