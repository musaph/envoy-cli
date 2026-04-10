"""CLI subcommands for merging .env files."""
import argparse
from pathlib import Path

from envoy.env_merge import EnvMerger, MergeStrategy
from envoy.parser import EnvParser


def register_merge_subcommands(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("merge", help="Merge two .env files")
    sub = p.add_subparsers(dest="merge_cmd")

    run_p = sub.add_parser("run", help="Merge a local and remote .env file")
    run_p.add_argument("local", help="Path to local .env file")
    run_p.add_argument("remote", help="Path to remote .env file")
    run_p.add_argument(
        "--strategy",
        choices=[s.value for s in MergeStrategy],
        default=MergeStrategy.LOCAL_WINS.value,
        help="Conflict resolution strategy (default: local_wins)",
    )
    run_p.add_argument("--output", "-o", help="Write merged result to this file")
    run_p.add_argument(
        "--show-conflicts", action="store_true", help="Print conflicts to stdout"
    )


def handle_merge_command(args: argparse.Namespace, out=print) -> int:
    if not hasattr(args, "merge_cmd") or args.merge_cmd is None:
        out("Usage: envoy merge <subcommand>  (run)")
        return 1

    if args.merge_cmd == "run":
        return _run_merge(args, out)

    out(f"Unknown merge subcommand: {args.merge_cmd}")
    return 1


def _run_merge(args: argparse.Namespace, out) -> int:
    local_path = Path(args.local)
    remote_path = Path(args.remote)

    if not local_path.exists():
        out(f"Error: local file not found: {local_path}")
        return 1
    if not remote_path.exists():
        out(f"Error: remote file not found: {remote_path}")
        return 1

    parser = EnvParser()
    local_vars = parser.parse(local_path.read_text())
    remote_vars = parser.parse(remote_path.read_text())

    strategy = MergeStrategy(args.strategy)
    merger = EnvMerger(strategy=strategy)
    result = merger.merge(local_vars, remote_vars)

    if args.show_conflicts and result.has_conflicts:
        out(f"Conflicts ({len(result.conflicts)}):")
        for key, (lv, rv) in result.conflicts.items():
            out(f"  {key}: local={lv!r}  remote={rv!r}")

    if strategy == MergeStrategy.INTERACTIVE and result.has_conflicts:
        out("Unresolved conflicts — aborting merge. Use --strategy to auto-resolve.")
        return 2

    serialized = parser.serialize(result.merged)
    if args.output:
        Path(args.output).write_text(serialized)
        out(f"Merged {len(result.merged)} variables -> {args.output}")
    else:
        out(serialized)

    return 0
