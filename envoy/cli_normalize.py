"""CLI subcommands for env-normalize: normalize .env variable values."""
from argparse import ArgumentParser, Namespace
from typing import Callable

from envoy.env_normalize import EnvNormalizer
from envoy.parser import EnvParser


def register_normalize_subcommands(subparsers) -> None:
    p: ArgumentParser = subparsers.add_parser(
        "normalize",
        help="Normalize variable values in a .env file",
    )
    p.add_argument("file", help="Path to the .env file")
    p.add_argument(
        "--no-strip-quotes",
        action="store_true",
        default=False,
        help="Do not strip outer quotes from values",
    )
    p.add_argument(
        "--no-fix-line-endings",
        action="store_true",
        default=False,
        help="Do not fix Windows-style line endings",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Show what would change without writing",
    )


def handle_normalize_command(args: Namespace, out: Callable = print) -> int:
    if not hasattr(args, "file"):
        out("Usage: envoy normalize <file> [options]")
        return 1

    import os
    if not os.path.isfile(args.file):
        out(f"Error: file not found: {args.file}")
        return 1

    parser = EnvParser()
    with open(args.file, "r", encoding="utf-8") as fh:
        content = fh.read()

    vars_ = parser.parse(content)
    normalizer = EnvNormalizer(
        strip_quotes=not args.no_strip_quotes,
        fix_line_endings=not args.no_fix_line_endings,
    )
    result = normalizer.normalize(vars_)

    if not result.has_changes:
        out("No normalization changes needed.")
        return 0

    for change in result.changes:
        out(f"  {change.key}: {change.original!r} -> {change.normalized!r} ({change.reason})")

    if args.dry_run:
        out(f"Dry run: {len(result.changes)} change(s) would be applied.")
        return 0

    serialized = parser.serialize(result.vars)
    with open(args.file, "w", encoding="utf-8") as fh:
        fh.write(serialized)

    out(f"Normalized {len(result.changes)} value(s) in {args.file}.")
    return 0
