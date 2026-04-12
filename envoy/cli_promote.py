"""CLI subcommands for the promote feature."""
from envoy.env_promote import EnvPromoter
from envoy.parser import EnvParser


def register_promote_subcommands(subparsers):
    p = subparsers.add_parser(
        "promote",
        help="Promote env vars from one file to another",
    )
    sub = p.add_subparsers(dest="promote_cmd")

    run_p = sub.add_parser("run", help="Run the promotion")
    run_p.add_argument("source", help="Source .env file")
    run_p.add_argument("target", help="Target .env file")
    run_p.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing keys in target",
    )
    run_p.add_argument(
        "--keys",
        nargs="+",
        metavar="KEY",
        help="Only promote these keys",
    )
    run_p.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing",
    )


def handle_promote_command(args, out=None):
    import sys
    out = out or sys.stdout

    if not hasattr(args, "promote_cmd") or args.promote_cmd is None:
        out.write("Usage: envoy promote <subcommand>\n")
        out.write("Subcommands: run\n")
        return 1

    if args.promote_cmd == "run":
        return _run_promote(args, out)

    out.write(f"Unknown promote subcommand: {args.promote_cmd}\n")
    return 1


def _run_promote(args, out):
    import os
    parser = EnvParser()

    if not os.path.isfile(args.source):
        out.write(f"Error: source file not found: {args.source}\n")
        return 1

    if not os.path.isfile(args.target):
        out.write(f"Error: target file not found: {args.target}\n")
        return 1

    with open(args.source) as f:
        source_vars = parser.parse(f.read())
    with open(args.target) as f:
        target_vars = parser.parse(f.read())

    promoter = EnvPromoter(
        overwrite=getattr(args, "overwrite", False),
        keys=getattr(args, "keys", None),
    )
    result, merged = promoter.promote(source_vars, target_vars)

    for change in result.added:
        out.write(f"  + {change.key}\n")
    for change in result.overwritten:
        out.write(f"  ~ {change.key} (overwritten)\n")
    for key in result.skipped:
        out.write(f"  - {key} (skipped, already exists)\n")

    if not result.has_changes:
        out.write("Nothing to promote.\n")
        return 0

    if getattr(args, "dry_run", False):
        out.write("Dry run — no files written.\n")
        return 0

    with open(args.target, "w") as f:
        f.write(EnvParser.serialize(merged))

    out.write(f"Promoted {len(result.added)} added, {len(result.overwritten)} overwritten.\n")
    return 0
