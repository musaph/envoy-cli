"""CLI subcommands for env-truncate feature."""
from envoy.env_truncate import EnvTruncator
from envoy.parser import EnvParser


def register_truncate_subcommands(subparsers):
    p = subparsers.add_parser("truncate", help="Truncate long env var values")
    sub = p.add_subparsers(dest="truncate_cmd")

    run_p = sub.add_parser("run", help="Truncate values in a .env file")
    run_p.add_argument("file", help="Path to .env file")
    run_p.add_argument(
        "--max-length", type=int, default=64, help="Maximum value length (default: 64)"
    )
    run_p.add_argument(
        "--suffix", default="...", help="Suffix appended to truncated values (default: ...)"
    )
    run_p.add_argument(
        "--skip", nargs="*", default=[], metavar="KEY", help="Keys to skip"
    )
    run_p.add_argument(
        "--dry-run", action="store_true", help="Show changes without writing"
    )


def handle_truncate_command(args, out=None):
    import sys
    out = out or sys.stdout

    if not hasattr(args, "truncate_cmd") or args.truncate_cmd is None:
        out.write("Usage: envoy truncate <subcommand>\n")
        return 1

    if args.truncate_cmd == "run":
        return _run_truncate(args, out)

    out.write(f"Unknown subcommand: {args.truncate_cmd}\n")
    return 1


def _run_truncate(args, out):
    import os
    if not os.path.isfile(args.file):
        out.write(f"Error: file not found: {args.file}\n")
        return 1

    parser = EnvParser()
    with open(args.file, "r") as fh:
        content = fh.read()

    vars_ = parser.parse(content)
    truncator = EnvTruncator(
        max_length=args.max_length,
        suffix=args.suffix,
        skip_keys=args.skip,
    )
    result = truncator.truncate(vars_)

    if not result.has_changes:
        out.write("No values exceed the maximum length.\n")
        return 0

    for change in result.changes:
        out.write(
            f"  {change.key}: {change.original_len} -> {change.truncated_len} chars\n"
        )

    if args.dry_run:
        out.write(f"Dry run: {len(result.changes)} value(s) would be truncated.\n")
        return 0

    updated = truncator.apply(vars_)
    new_content = parser.serialize(updated)
    with open(args.file, "w") as fh:
        fh.write(new_content)

    out.write(f"Truncated {len(result.changes)} value(s) in {args.file}\n")
    return 0
