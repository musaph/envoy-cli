"""CLI subcommands for env var pinning."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import IO

from envoy.env_pin import EnvPinner
from envoy.parser import EnvParser


def register_pin_subcommands(subparsers: argparse._SubParsersAction) -> None:
    pin_parser = subparsers.add_parser("pin", help="Pin env vars to required values")
    pin_sub = pin_parser.add_subparsers(dest="pin_cmd")

    check_p = pin_sub.add_parser("check", help="Check pins against an env file")
    check_p.add_argument("file", help="Path to .env file")
    check_p.add_argument(
        "--pins", required=True,
        help="JSON object mapping key->value or key->re:pattern"
    )

    apply_p = pin_sub.add_parser("apply", help="Apply literal pins to an env file")
    apply_p.add_argument("file", help="Path to .env file")
    apply_p.add_argument(
        "--pins", required=True,
        help="JSON object mapping key->value"
    )
    apply_p.add_argument("--output", default=None, help="Output file (default: overwrite)")


def handle_pin_command(args: argparse.Namespace, out: IO[str] = sys.stdout) -> int:
    if not hasattr(args, "pin_cmd") or args.pin_cmd is None:
        out.write("Usage: envoy pin <check|apply>\n")
        return 1

    try:
        pins = json.loads(args.pins)
    except json.JSONDecodeError as exc:
        out.write(f"Error: invalid --pins JSON: {exc}\n")
        return 1

    env_path = Path(args.file)
    if not env_path.exists():
        out.write(f"Error: file not found: {env_path}\n")
        return 1

    parser = EnvParser()
    vars = parser.parse(env_path.read_text())
    pinner = EnvPinner(pins=pins)

    if args.pin_cmd == "check":
        result = pinner.check(vars)
        if result.is_clean:
            out.write(f"All {result.pinned_count} pin(s) satisfied.\n")
            return 0
        else:
            for v in result.violations:
                out.write(f"  VIOLATION [{v.key}]: {v.reason}")
                if v.actual is not None:
                    out.write(f" (got {v.actual!r}, expected {v.expected!r})")
                out.write("\n")
            return 1

    if args.pin_cmd == "apply":
        updated = pinner.apply(vars)
        serialized = EnvParser.serialize(updated)
        dest = Path(args.output) if args.output else env_path
        dest.write_text(serialized)
        out.write(f"Pins applied to {dest}\n")
        return 0

    out.write(f"Unknown pin subcommand: {args.pin_cmd}\n")
    return 1
