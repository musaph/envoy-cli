import argparse
from typing import IO

from envoy.env_replace import EnvReplacer
from envoy.parser import EnvParser


def register_replace_subcommands(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("replace", help="Replace substrings in .env values")
    sub = p.add_subparsers(dest="replace_cmd")

    run_p = sub.add_parser("run", help="Perform replacement in an env file")
    run_p.add_argument("file", help="Path to .env file")
    run_p.add_argument("pattern", help="Substring to find")
    run_p.add_argument("replacement", help="Replacement string")
    run_p.add_argument(
        "--keys", nargs="+", metavar="KEY", help="Limit replacement to these keys"
    )
    run_p.add_argument(
        "--dry-run", action="store_true", help="Show changes without writing"
    )


def handle_replace_command(args: argparse.Namespace, out: IO[str]) -> int:
    if not hasattr(args, "replace_cmd") or args.replace_cmd is None:
        out.write("Usage: envoy replace <subcommand>\n")
        return 1

    if args.replace_cmd == "run":
        return _run_replace(args, out)

    out.write(f"Unknown replace subcommand: {args.replace_cmd}\n")
    return 1


def _run_replace(args: argparse.Namespace, out: IO[str]) -> int:
    try:
        with open(args.file) as f:
            content = f.read()
    except FileNotFoundError:
        out.write(f"Error: file not found: {args.file}\n")
        return 1

    parser = EnvParser()
    vars_ = parser.parse(content)

    replacer = EnvReplacer(
        pattern=args.pattern,
        replacement=args.replacement,
        keys=args.keys if args.keys else None,
    )
    result = replacer.replace(vars_)

    if not result.has_changes():
        out.write("No replacements made.\n")
        return 0

    for change in result.changes:
        out.write(f"  {change.key}: {change.old_value!r} -> {change.new_value!r}\n")

    if args.dry_run:
        out.write(f"Dry run: {len(result.changes)} change(s) not written.\n")
        return 0

    updated = replacer.apply(vars_)
    new_content = parser.serialize(updated)
    with open(args.file, "w") as f:
        f.write(new_content)

    out.write(f"Replaced {len(result.changes)} value(s) in {args.file}\n")
    return 0
