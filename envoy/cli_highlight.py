import argparse
from typing import List

from envoy.env_highlight import EnvHighlighter
from envoy.parser import EnvParser


def register_highlight_subcommands(subparsers) -> None:
    p = subparsers.add_parser("highlight", help="Highlight .env vars matching patterns")
    sub = p.add_subparsers(dest="highlight_cmd")

    scan = sub.add_parser("scan", help="Scan a .env file for pattern matches")
    scan.add_argument("file", help="Path to .env file")
    scan.add_argument("patterns", nargs="+", help="Regex patterns to match")
    scan.add_argument("--keys-only", action="store_true", help="Match keys only, not values")
    scan.add_argument("--case-sensitive", action="store_true", help="Enable case-sensitive matching")


def handle_highlight_command(args, output=None) -> int:
    import sys
    out = output or sys.stdout

    if not hasattr(args, "highlight_cmd") or args.highlight_cmd is None:
        out.write("Usage: envoy highlight <subcommand>\n")
        out.write("Subcommands: scan\n")
        return 1

    if args.highlight_cmd == "scan":
        return _run_scan(args, out)

    out.write(f"Unknown subcommand: {args.highlight_cmd}\n")
    return 1


def _run_scan(args, out) -> int:
    import os
    if not os.path.exists(args.file):
        out.write(f"Error: file not found: {args.file}\n")
        return 1

    with open(args.file) as f:
        content = f.read()

    parser = EnvParser()
    vars = parser.parse(content)

    case_sensitive = getattr(args, "case_sensitive", False)
    keys_only = getattr(args, "keys_only", False)

    highlighter = EnvHighlighter(patterns=args.patterns, case_sensitive=case_sensitive)

    if keys_only:
        result = highlighter.highlight_keys_only(vars)
    else:
        result = highlighter.highlight(vars)

    if not result.found:
        out.write("No matches found.\n")
        return 0

    out.write(f"Found {len(result.matches)} match(es):\n")
    for match in result.matches:
        out.write(f"  {match.key}={match.value!r}  (pattern: {match.pattern})\n")

    return 0
