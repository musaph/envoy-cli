import argparse
from typing import Callable

from envoy.env_prefix import EnvPrefixer
from envoy.parser import EnvParser


def register_prefix_subcommands(sub: argparse.ArgumentParser) -> None:
    sub.add_argument("file", help="Path to .env file")
    sub.add_argument("prefix", help="Prefix string (e.g. APP)")
    sub.add_argument(
        "action",
        choices=["add", "remove", "filter"],
        help="Operation to perform on the prefix",
    )
    sub.add_argument(
        "--separator",
        default="_",
        help="Separator between prefix and key (default: _)",
    )
    sub.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without writing to file",
    )


def handle_prefix_command(args: argparse.Namespace, out: Callable = print) -> int:
    if not hasattr(args, "file"):
        out("Usage: envoy prefix <file> <prefix> <add|remove|filter>")
        return 1

    try:
        with open(args.file, "r") as fh:
            content = fh.read()
    except FileNotFoundError:
        out(f"Error: file not found: {args.file}")
        return 1

    parser = EnvParser()
    vars_ = parser.parse(content)

    try:
        prefixer = EnvPrefixer(prefix=args.prefix, separator=args.separator)
    except ValueError as exc:
        out(f"Error: {exc}")
        return 1

    if args.action == "add":
        result = prefixer.add(vars_)
        for change in result.changes:
            out(f"  + {change.key} -> {change.new_key}")
        for key in result.skipped:
            out(f"  ~ {key} (already prefixed, skipped)")
        if not args.dry_run:
            with open(args.file, "w") as fh:
                fh.write(parser.serialize(result.renamed))
        out(f"Done: {len(result.changes)} key(s) renamed.")

    elif args.action == "remove":
        result = prefixer.remove(vars_)
        for change in result.changes:
            out(f"  - {change.key} -> {change.new_key}")
        for key in result.skipped:
            out(f"  ~ {key} (no prefix, skipped)")
        if not args.dry_run:
            with open(args.file, "w") as fh:
                fh.write(parser.serialize(result.renamed))
        out(f"Done: {len(result.changes)} key(s) renamed.")

    elif args.action == "filter":
        filtered = prefixer.filter(vars_)
        if not filtered:
            out(f"No variables found with prefix '{args.prefix}'.")
        else:
            for key, value in filtered.items():
                out(f"  {key}={value}")

    return 0
