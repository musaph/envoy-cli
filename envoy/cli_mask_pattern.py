"""CLI subcommands for env-mask-pattern feature."""
import argparse
import re
from pathlib import Path
from typing import Optional

from envoy.env_mask_pattern import EnvMaskPattern
from envoy.parser import EnvParser


def register_mask_pattern_subcommands(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("mask-pattern", help="Mask env var values by key or value pattern")
    sub = p.add_subparsers(dest="mask_pattern_cmd")

    ap = sub.add_parser("apply", help="Apply masking to a .env file")
    ap.add_argument("file", help="Path to .env file")
    ap.add_argument("--key-pattern", dest="key_patterns", action="append",
                    metavar="REGEX", help="Regex pattern to match against keys (repeatable)")
    ap.add_argument("--value-pattern", dest="value_pattern", metavar="REGEX",
                    help="Regex pattern to match against values")
    ap.add_argument("--reveal-chars", dest="reveal_chars", type=int, default=0,
                    help="Number of leading chars to keep unmasked")
    ap.add_argument("--show-all", action="store_true",
                    help="Print all vars, not just changed ones")


def handle_mask_pattern_command(args: argparse.Namespace, out=print) -> int:
    if not hasattr(args, "mask_pattern_cmd") or args.mask_pattern_cmd is None:
        out("Usage: envoy mask-pattern <apply>")
        return 1

    if args.mask_pattern_cmd == "apply":
        path = Path(args.file)
        if not path.exists():
            out(f"Error: file not found: {path}")
            return 2

        parser = EnvParser()
        vars_ = parser.parse(path.read_text())

        key_patterns = None
        if args.key_patterns:
            try:
                key_patterns = [re.compile(p, re.IGNORECASE) for p in args.key_patterns]
            except re.error as exc:
                out(f"Error: invalid key pattern: {exc}")
                return 3

        value_pattern: Optional[re.Pattern] = None
        if args.value_pattern:
            try:
                value_pattern = re.compile(args.value_pattern)
            except re.error as exc:
                out(f"Error: invalid value pattern: {exc}")
                return 3

        masker = EnvMaskPattern(
            key_patterns=key_patterns,
            value_pattern=value_pattern,
            reveal_chars=args.reveal_chars,
        )
        result = masker.apply(vars_)

        if not result.has_changes:
            out("No values masked.")
        else:
            out(f"Masked {len(result.changes)} variable(s):")
            for change in result.changes:
                out(f"  {change.key}: {change.masked}")

        if getattr(args, "show_all", False):
            out("\nAll variables after masking:")
            for k, v in result.output.items():
                out(f"  {k}={v}")

        return 0

    out(f"Unknown subcommand: {args.mask_pattern_cmd}")
    return 1
