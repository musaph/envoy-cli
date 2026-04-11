"""CLI subcommands for env variable comparison."""
import argparse
from typing import IO
import sys

from envoy.env_compare import EnvComparer
from envoy.parser import EnvParser


def register_compare_subcommands(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("compare", help="Compare two .env files")
    sub = p.add_subparsers(dest="compare_cmd")

    run_p = sub.add_parser("run", help="Run comparison between two env files")
    run_p.add_argument("local", help="Path to local .env file")
    run_p.add_argument("remote", help="Path to remote/reference .env file")
    run_p.add_argument(
        "--only-diff",
        action="store_true",
        help="Show only differing / missing keys",
    )


def handle_compare_command(
    args: argparse.Namespace,
    out: IO[str] = sys.stdout,
) -> int:
    if not hasattr(args, "compare_cmd") or args.compare_cmd is None:
        out.write("Usage: envoy compare <subcommand>\n")
        out.write("Subcommands: run\n")
        return 1

    if args.compare_cmd == "run":
        return _run_compare(args, out)

    out.write(f"Unknown compare subcommand: {args.compare_cmd}\n")
    return 1


def _run_compare(args: argparse.Namespace, out: IO[str]) -> int:
    parser = EnvParser()
    comparer = EnvComparer()

    try:
        with open(args.local) as fh:
            local_vars = parser.parse(fh.read())
    except FileNotFoundError:
        out.write(f"Error: local file not found: {args.local}\n")
        return 1

    try:
        with open(args.remote) as fh:
            remote_vars = parser.parse(fh.read())
    except FileNotFoundError:
        out.write(f"Error: remote file not found: {args.remote}\n")
        return 1

    report = comparer.compare(local_vars, remote_vars)

    only_diff = getattr(args, "only_diff", False)

    if not only_diff:
        for entry in report.matches:
            out.write(f"  [=] {entry.key}\n")

    for entry in report.differences:
        out.write(f"  [~] {entry.key}: local={entry.local_value!r} remote={entry.remote_value!r}\n")

    for entry in report.local_only:
        out.write(f"  [+] {entry.key} (local only)\n")

    for entry in report.remote_only:
        out.write(f"  [-] {entry.key} (remote only)\n")

    out.write(f"\nSummary: {repr(report)}\n")
    return 0
