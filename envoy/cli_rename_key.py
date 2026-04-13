import argparse
from typing import List

from envoy.env_rename_key import EnvKeyRenamer


def register_rename_key_subcommands(subparsers) -> None:
    p = subparsers.add_parser("rename-key", help="Rename one or more keys in a .env file")
    p.add_argument("file", help="Path to the .env file")
    p.add_argument(
        "--map",
        metavar="OLD=NEW",
        action="append",
        required=True,
        help="Rename mapping in OLD=NEW format (repeatable)",
    )
    p.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Allow overwriting an existing target key",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Show what would change without writing",
    )


def handle_rename_key_command(args, out=None) -> int:
    import sys
    from envoy.parser import EnvParser

    out = out or sys.stdout

    if not hasattr(args, "file"):
        out.write("Usage: envoy rename-key <file> --map OLD=NEW [--overwrite] [--dry-run]\n")
        return 1

    import os
    if not os.path.isfile(args.file):
        out.write(f"Error: file not found: {args.file}\n")
        return 1

    mapping = {}
    for entry in (args.map or []):
        if "=" not in entry:
            out.write(f"Error: invalid mapping {entry!r}, expected OLD=NEW format\n")
            return 1
        old, new = entry.split("=", 1)
        mapping[old.strip()] = new.strip()

    with open(args.file, "r") as fh:
        raw = fh.read()

    parser = EnvParser()
    vars_ = parser.parse(raw)

    renamer = EnvKeyRenamer(overwrite=getattr(args, "overwrite", False))
    result = renamer.rename(vars_, mapping)

    for err in result.errors:
        out.write(f"Error: {err}\n")

    for change in result.changes:
        out.write(f"Renamed: {change.old_key} -> {change.new_key}\n")

    for key in result.skipped:
        out.write(f"Skipped: {key}\n")

    if result.errors:
        return 1

    if not getattr(args, "dry_run", False) and result.has_changes:
        updated = renamer.apply(vars_, mapping)
        serialized = parser.serialize(updated)
        with open(args.file, "w") as fh:
            fh.write(serialized)
        out.write(f"Written: {args.file}\n")

    return 0
