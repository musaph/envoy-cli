from envoy.env_reorder import EnvReorderer
from envoy.parser import EnvParser


def register_reorder_subcommands(subparsers):
    p = subparsers.add_parser("reorder", help="Reorder variables in a .env file")
    sub = p.add_subparsers(dest="reorder_cmd")

    run_p = sub.add_parser("run", help="Reorder variables")
    run_p.add_argument("file", help="Path to .env file")
    run_p.add_argument(
        "--alphabetical", action="store_true", help="Sort keys alphabetically"
    )
    run_p.add_argument(
        "--order",
        nargs="+",
        metavar="KEY",
        help="Explicit key order (remaining keys appended)",
    )
    run_p.add_argument(
        "--write", action="store_true", help="Write result back to file"
    )


def handle_reorder_command(args, out=None):
    import sys

    out = out or sys.stdout

    if not hasattr(args, "reorder_cmd") or args.reorder_cmd is None:
        out.write("Usage: envoy reorder <subcommand>\n")
        return 1

    if args.reorder_cmd == "run":
        import os

        if not os.path.exists(args.file):
            out.write(f"Error: file not found: {args.file}\n")
            return 1

        with open(args.file) as fh:
            content = fh.read()

        parser = EnvParser()
        vars_ = parser.parse(content)

        reorderer = EnvReorderer(
            order=getattr(args, "order", None) or [],
            alphabetical=getattr(args, "alphabetical", False),
        )
        result = reorderer.reorder(vars_)

        if not result.has_changes:
            out.write("No changes — already in desired order.\n")
            return 0

        out.write(f"Reordered {len(result.changes)} key(s):\n")
        for ch in result.changes:
            out.write(f"  {ch.key}: position {ch.old_index} -> {ch.new_index}\n")

        if getattr(args, "write", False):
            serialized = parser.serialize(result.reordered)
            with open(args.file, "w") as fh:
                fh.write(serialized)
            out.write(f"Written to {args.file}\n")

        return 0

    out.write(f"Unknown subcommand: {args.reorder_cmd}\n")
    return 1
