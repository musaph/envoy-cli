"""CLI subcommands for env-diff-summary."""
import argparse
import json
from pathlib import Path
from typing import Optional

from envoy.env_diff_summary import EnvDiffSummarizer
from envoy.parser import EnvParser


def register_diff_summary_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("diff-summary", help="Summarise differences between two .env files")
    p.add_argument("old_file", help="Path to the old/base .env file")
    p.add_argument("new_file", help="Path to the new .env file")
    p.add_argument("--ignore-case", action="store_true", help="Treat values as case-insensitive")
    p.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    p.add_argument("--only-changes", action="store_true", help="Omit unchanged keys from output")


def handle_diff_summary_command(args: argparse.Namespace, out=print) -> int:
    if not hasattr(args, "old_file"):
        out("Usage: envoy diff-summary <old_file> <new_file> [options]")
        return 1

    old_path = Path(args.old_file)
    new_path = Path(args.new_file)

    if not old_path.exists():
        out(f"Error: file not found: {old_path}")
        return 1
    if not new_path.exists():
        out(f"Error: file not found: {new_path}")
        return 1

    parser = EnvParser()
    old_vars = parser.parse(old_path.read_text())
    new_vars = parser.parse(new_path.read_text())

    summarizer = EnvDiffSummarizer(ignore_case=getattr(args, "ignore_case", False))
    result = summarizer.summarise(old_vars, new_vars)

    only_changes = getattr(args, "only_changes", False)
    fmt = getattr(args, "format", "text")

    entries = result.entries if not only_changes else (
        result.added + result.removed + result.changed
    )

    if fmt == "json":
        data = [
            {"key": e.key, "status": e.status, "old": e.old_value, "new": e.new_value}
            for e in entries
        ]
        out(json.dumps(data, indent=2))
    else:
        if not result.has_differences and not only_changes:
            out("No differences found.")
        else:
            symbols = {"added": "+", "removed": "-", "changed": "~", "unchanged": " "}
            for e in entries:
                sym = symbols.get(e.status, "?")
                if e.status == "changed":
                    out(f"{sym} {e.key}: {e.old_value!r} -> {e.new_value!r}")
                elif e.status == "added":
                    out(f"{sym} {e.key}={e.new_value!r}")
                elif e.status == "removed":
                    out(f"{sym} {e.key}={e.old_value!r}")
                else:
                    out(f"{sym} {e.key}")
        out(f"\nSummary: +{len(result.added)} -{len(result.removed)} ~{len(result.changed)} ={len(result.unchanged)}")

    return 0
