import argparse
from typing import Any, Dict

from envoy.env_copy import EnvCopier


def register_copy_subcommands(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "copy",
        help="Copy env variable values to new keys",
    )
    parser.add_argument("file", help="Path to the .env file")
    parser.add_argument(
        "--map",
        metavar="SRC:DST",
        action="append",
        dest="mappings",
        required=True,
        help="Mapping in the form SOURCE_KEY:DEST_KEY (repeatable)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Allow overwriting existing destination keys",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Preview changes without writing to file",
    )


def handle_copy_command(args: Any, out=print) -> int:
    if not hasattr(args, "file"):
        out("Usage: envoy copy <file> --map SRC:DST [--overwrite] [--dry-run]")
        return 1

    import os
    from envoy.parser import EnvParser

    if not os.path.isfile(args.file):
        out(f"Error: file not found: {args.file}")
        return 1

    with open(args.file, "r") as fh:
        raw = fh.read()

    parser = EnvParser()
    vars: Dict[str, str] = parser.parse(raw)

    mappings: Dict[str, str] = {}
    for entry in args.mappings:
        if ":" not in entry:
            out(f"Error: invalid mapping {entry!r}; expected SRC:DST")
            return 1
        src, dst = entry.split(":", 1)
        mappings[src.strip()] = dst.strip()

    copier = EnvCopier(overwrite=args.overwrite)
    result = copier.copy(vars, mappings)

    for err in result.errors:
        out(f"Error: {err}")

    for change in result.changes:
        out(f"  copy {change.source_key!r} -> {change.dest_key!r}")

    if result.has_errors:
        return 1

    if not result.has_changes:
        out("No changes to apply.")
        return 0

    if args.dry_run:
        out("Dry run — no changes written.")
        return 0

    updated = {**vars}
    for change in result.changes:
        updated[change.dest_key] = change.value

    with open(args.file, "w") as fh:
        fh.write(parser.serialize(updated))

    out(f"Copied {len(result.changes)} key(s) in {args.file}")
    return 0
