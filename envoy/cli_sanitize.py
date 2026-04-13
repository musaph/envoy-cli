from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from envoy.env_sanitize import EnvSanitizer
from envoy.parser import EnvParser


def register_sanitize_subcommands(subparsers) -> None:
    p = subparsers.add_parser("sanitize", help="Sanitize .env file values")
    sub = p.add_subparsers(dest="sanitize_cmd")

    run_p = sub.add_parser("run", help="Sanitize values in an env file")
    run_p.add_argument("file", help="Path to .env file")
    run_p.add_argument("--no-strip", action="store_true", help="Disable whitespace stripping")
    run_p.add_argument("--no-control", action="store_true", help="Disable control char removal")
    run_p.add_argument("--max-length", type=int, default=None, help="Maximum value length")
    run_p.add_argument("--in-place", action="store_true", help="Overwrite file with sanitized values")


def handle_sanitize_command(args, out=None) -> int:
    import sys
    out = out or sys.stdout

    if not hasattr(args, "sanitize_cmd") or args.sanitize_cmd is None:
        out.write("Usage: envoy sanitize <subcommand>\n")
        out.write("Subcommands: run\n")
        return 1

    if args.sanitize_cmd == "run":
        return _run_sanitize(args, out)

    out.write(f"Unknown sanitize subcommand: {args.sanitize_cmd}\n")
    return 1


def _run_sanitize(args, out) -> int:
    path = Path(args.file)
    if not path.exists():
        out.write(f"Error: file not found: {path}\n")
        return 1

    parser = EnvParser()
    vars_ = parser.parse(path.read_text())

    sanitizer = EnvSanitizer(
        strip_whitespace=not args.no_strip,
        remove_control_chars=not args.no_control,
        max_length=args.max_length,
    )
    result = sanitizer.sanitize(vars_)

    if not result.has_changes:
        out.write("No sanitization needed.\n")
        return 0

    out.write(f"Sanitized {len(result.changes)} value(s):\n")
    for change in result.changes:
        out.write(f"  {change.key}: {change.reason}\n")

    if args.in_place:
        from envoy.parser import EnvParser as _P
        serialized = EnvParser().serialize(result.sanitized)
        path.write_text(serialized)
        out.write(f"Written to {path}\n")

    return 0
