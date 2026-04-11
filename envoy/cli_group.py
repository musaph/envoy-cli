"""CLI subcommands for env variable grouping."""
from typing import Any
from envoy.env_group import EnvGrouper
from envoy.parser import EnvParser


def register_group_subcommands(subparsers: Any) -> None:
    group_parser = subparsers.add_parser("group", help="Group env vars by prefix")
    group_sub = group_parser.add_subparsers(dest="group_cmd")

    show = group_sub.add_parser("show", help="Display grouped variables")
    show.add_argument("file", help="Path to .env file")
    show.add_argument(
        "--prefixes", nargs="*", metavar="PREFIX",
        help="Explicit prefixes to group by (auto-detected if omitted)"
    )
    show.add_argument(
        "--min-size", type=int, default=2, metavar="N",
        help="Minimum group size for auto-detection (default: 2)"
    )


def handle_group_command(args: Any, out=print) -> int:
    if not hasattr(args, "group_cmd") or args.group_cmd is None:
        out("Usage: envoy group <show>")
        return 1

    if args.group_cmd == "show":
        return _show(args, out)

    out(f"Unknown group subcommand: {args.group_cmd}")
    return 1


def _show(args: Any, out) -> int:
    import os
    if not os.path.exists(args.file):
        out(f"Error: file not found: {args.file}")
        return 1

    with open(args.file) as fh:
        raw = fh.read()

    parser = EnvParser()
    vars_ = parser.parse(raw)

    grouper = EnvGrouper(min_group_size=args.min_size)
    prefixes = args.prefixes if args.prefixes else None
    result = grouper.group_by_prefix(vars_, prefixes=prefixes)

    for prefix, group_vars in sorted(result.groups.items()):
        out(f"[{prefix}]")
        for k, v in sorted(group_vars.items()):
            out(f"  {k}={v}")

    if result.ungrouped:
        out("[ungrouped]")
        for k, v in sorted(result.ungrouped.items()):
            out(f"  {k}={v}")

    out(f"\n{len(result.groups)} group(s), {len(result.ungrouped)} ungrouped var(s)")
    return 0
