"""CLI subcommands for snapshot-diff: compare two env snapshots."""
from __future__ import annotations
import json
from pathlib import Path
from envoy.snapshot import Snapshot
from envoy.env_snapshot_diff import SnapshotDiffer


def register_snapshot_diff_subcommands(subparsers) -> None:
    p = subparsers.add_parser("snapshot-diff", help="Diff two env snapshots")
    sub = p.add_subparsers(dest="snapshot_diff_cmd")

    cmp = sub.add_parser("compare", help="Compare two snapshot JSON files")
    cmp.add_argument("old", help="Path to the older snapshot JSON file")
    cmp.add_argument("new", help="Path to the newer snapshot JSON file")
    cmp.add_argument(
        "--show-unchanged",
        action="store_true",
        default=False,
        help="Also display unchanged keys",
    )


def handle_snapshot_diff_command(args, out=None) -> int:
    import sys

    out = out or sys.stdout

    if not hasattr(args, "snapshot_diff_cmd") or args.snapshot_diff_cmd is None:
        out.write("Usage: envoy snapshot-diff <compare>\n")
        return 1

    if args.snapshot_diff_cmd == "compare":
        return _run_compare(args, out)

    out.write(f"Unknown snapshot-diff subcommand: {args.snapshot_diff_cmd}\n")
    return 1


def _run_compare(args, out) -> int:
    old_path = Path(args.old)
    new_path = Path(args.new)

    for p in (old_path, new_path):
        if not p.exists():
            out.write(f"Error: file not found: {p}\n")
            return 1

    try:
        old_snap = Snapshot.from_dict(json.loads(old_path.read_text()))
        new_snap = Snapshot.from_dict(json.loads(new_path.read_text()))
    except (KeyError, ValueError) as exc:
        out.write(f"Error loading snapshot: {exc}\n")
        return 1

    differ = SnapshotDiffer()
    result = differ.diff(old_snap, new_snap)

    out.write(f"Comparing: {result.old_label}  →  {result.new_label}\n")
    out.write(f"Added: {len(result.added())}  Removed: {len(result.removed())}  "
              f"Changed: {len(result.changed())}\n\n")

    for entry in result.entries:
        if entry.status == "added":
            out.write(f"  + {entry.key}={entry.new_value}\n")
        elif entry.status == "removed":
            out.write(f"  - {entry.key}={entry.old_value}\n")
        elif entry.status == "changed":
            out.write(f"  ~ {entry.key}: {entry.old_value!r} → {entry.new_value!r}\n")
        elif getattr(args, "show_unchanged", False):
            out.write(f"    {entry.key}={entry.old_value}\n")

    return 0
