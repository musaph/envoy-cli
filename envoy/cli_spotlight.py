"""CLI subcommands for env-spotlight."""
from __future__ import annotations
from typing import List

from envoy.env_spotlight import EnvSpotlight
from envoy.parser import EnvParser


def register_spotlight_subcommands(subparsers) -> None:
    p = subparsers.add_parser("spotlight", help="Surface prioritised env vars")
    sub = p.add_subparsers(dest="spotlight_cmd")

    scan_p = sub.add_parser("scan", help="Scan a .env file against priority patterns")
    scan_p.add_argument("file", help="Path to .env file")
    scan_p.add_argument(
        "--pattern",
        dest="patterns",
        action="append",
        default=[],
        metavar="REGEX",
        help="Pattern to match (repeatable, order = priority)",
    )
    scan_p.add_argument(
        "--case-sensitive", action="store_true", default=False
    )
    scan_p.add_argument(
        "--show-unmatched", action="store_true", default=False
    )


def handle_spotlight_command(args, out=None) -> int:
    import sys

    out = out or sys.stdout

    if not hasattr(args, "spotlight_cmd") or args.spotlight_cmd is None:
        out.write("Usage: envoy spotlight <subcommand>\n")
        return 1

    if args.spotlight_cmd == "scan":
        return _run_scan(args, out)

    out.write(f"Unknown subcommand: {args.spotlight_cmd}\n")
    return 1


def _run_scan(args, out) -> int:
    try:
        content = open(args.file).read()
    except FileNotFoundError:
        out.write(f"Error: file not found: {args.file}\n")
        return 2

    patterns: List[str] = args.patterns
    if not patterns:
        out.write("Error: at least one --pattern is required\n")
        return 1

    parser = EnvParser()
    vars_ = parser.parse(content)
    spotlight = EnvSpotlight(patterns, case_sensitive=args.case_sensitive)
    result = spotlight.scan(vars_)

    if not result.found:
        out.write("No matches found.\n")
    else:
        out.write(f"Spotlight matches ({len(result.matches)}):\n")
        for m in result.matches:
            out.write(f"  [P{m.priority}] {m.key}={m.value}  (pattern: {m.pattern})\n")

    if args.show_unmatched and result.unmatched_keys:
        out.write(f"\nUnmatched ({len(result.unmatched_keys)}):\n")
        for k in sorted(result.unmatched_keys):
            out.write(f"  {k}\n")

    return 0
