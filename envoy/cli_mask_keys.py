import argparse
from typing import Callable, Optional

from envoy.env_mask_keys import EnvKeyMasker
from envoy.parser import EnvParser


def register_mask_keys_subcommands(subparsers) -> None:
    p = subparsers.add_parser("mask-keys", help="Mask environment variable key names")
    sub = p.add_subparsers(dest="mask_keys_cmd")

    run_p = sub.add_parser("run", help="Mask keys in a .env file")
    run_p.add_argument("file", help="Path to the .env file")
    run_p.add_argument(
        "--visible",
        type=int,
        default=2,
        help="Number of visible leading characters (default: 2)",
    )
    run_p.add_argument(
        "--char",
        default="*",
        help="Mask character to use (default: *)",
    )
    run_p.add_argument(
        "--keys",
        nargs="*",
        help="Specific keys to mask (default: all keys)",
    )


def handle_mask_keys_command(
    args,
    out: Optional[Callable[[str], None]] = None,
) -> int:
    if out is None:
        out = print

    cmd = getattr(args, "mask_keys_cmd", None)
    if cmd is None:
        out("Usage: envoy mask-keys <subcommand>")
        out("Subcommands: run")
        return 1

    if cmd == "run":
        return _run_mask_keys(args, out)

    out(f"Unknown subcommand: {cmd}")
    return 1


def _run_mask_keys(args, out: Callable[[str], None]) -> int:
    try:
        with open(args.file, "r") as fh:
            content = fh.read()
    except FileNotFoundError:
        out(f"Error: file not found: {args.file}")
        return 1

    parser = EnvParser()
    vars_ = parser.parse(content)

    masker = EnvKeyMasker(
        mask_char=args.char,
        visible_chars=args.visible,
        keys=args.keys if args.keys else None,
    )
    result = masker.mask(vars_)

    if not result.has_changes():
        out("No keys were masked.")
        return 0

    out(f"Masked {len(result.changes)} key(s):")
    for change in result.changes:
        out(f"  {change.original_key!r} -> {change.masked_key!r}")

    return 0
