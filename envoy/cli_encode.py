from __future__ import annotations
import argparse
from typing import Callable

from envoy.env_encode import EnvEncoder, SUPPORTED_ENCODINGS
from envoy.parser import EnvParser


def register_encode_subcommands(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("encode", help="Encode env variable values")
    sub = p.add_subparsers(dest="encode_cmd")

    run_p = sub.add_parser("run", help="Encode values in an env file")
    run_p.add_argument("file", help="Path to the .env file")
    run_p.add_argument(
        "--encoding",
        choices=SUPPORTED_ENCODINGS,
        default="url",
        help="Encoding to apply (default: url)",
    )
    run_p.add_argument(
        "--keys",
        nargs="+",
        metavar="KEY",
        help="Limit encoding to specific keys",
    )
    run_p.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without modifying the file",
    )


def handle_encode_command(
    args: argparse.Namespace,
    print_fn: Callable[[str], None] = print,
) -> int:
    if not hasattr(args, "encode_cmd") or args.encode_cmd is None:
        print_fn("Usage: envoy encode <subcommand>  (run)")
        return 1

    if args.encode_cmd == "run":
        return _run_encode(args, print_fn)

    print_fn(f"Unknown encode subcommand: {args.encode_cmd}")
    return 1


def _run_encode(
    args: argparse.Namespace,
    print_fn: Callable[[str], None],
) -> int:
    import os

    if not os.path.exists(args.file):
        print_fn(f"Error: file not found: {args.file}")
        return 1

    parser = EnvParser()
    with open(args.file) as fh:
        content = fh.read()

    vars_ = parser.parse(content)
    encoder = EnvEncoder(encoding=args.encoding, keys=args.keys)
    result = encoder.encode(vars_)

    if not result.has_changes():
        print_fn("No values required encoding.")
        return 0

    for change in result.changes:
        print_fn(f"  {change.key}: {change.original!r} -> {change.encoded!r}")

    if args.dry_run:
        print_fn(f"Dry run: {len(result.changes)} value(s) would be encoded.")
        return 0

    encoded_vars = encoder.apply(vars_)
    new_content = parser.serialize(encoded_vars)
    with open(args.file, "w") as fh:
        fh.write(new_content)

    print_fn(f"Encoded {len(result.changes)} value(s) using '{args.encoding}'.")
    return 0
