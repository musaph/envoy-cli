"""CLI subcommands for importing .env files from various formats."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envoy.import_export_env import EnvImporter
from envoy.parser import EnvParser


def register_import_subcommands(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("import", help="Import env vars from dotenv/JSON/YAML")
    p.add_argument("file", help="Path to the source file")
    p.add_argument("--format", choices=["dotenv", "json", "yaml"],
                   default=None, help="Force a specific format (auto-detected by default)")
    p.add_argument("--output", default=None,
                   help="Write result as .env to this path (default: stdout)")
    p.add_argument("--merge", default=None,
                   help="Merge into an existing .env file (existing keys take precedence)")


def handle_import_command(args: argparse.Namespace,
                          out=sys.stdout, err=sys.stderr) -> int:
    if not hasattr(args, "file"):
        err.write("Usage: envoy import <file> [--format dotenv|json|yaml]\n")
        return 1

    src = Path(args.file)
    if not src.exists():
        err.write(f"Error: file not found: {src}\n")
        return 1

    content = src.read_text(encoding="utf-8")
    importer = EnvImporter()

    try:
        result = importer.load(content, source=str(src), fmt=args.format)
    except Exception as exc:  # noqa: BLE001
        err.write(f"Error parsing {src}: {exc}\n")
        return 1

    merged_vars = dict(result.vars)

    if args.merge:
        merge_path = Path(args.merge)
        if merge_path.exists():
            existing = EnvParser().parse(merge_path.read_text(encoding="utf-8"))
            # Existing keys win
            merged_vars.update({k: v for k, v in existing.items()})

    serialized = EnvParser().serialize(merged_vars)

    if args.output:
        Path(args.output).write_text(serialized, encoding="utf-8")
        out.write(f"Imported {len(merged_vars)} variable(s) -> {args.output}\n")
    else:
        out.write(serialized)

    return 0
