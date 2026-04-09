"""CLI subcommands for the export feature."""
from __future__ import annotations

import argparse
import sys
from typing import Optional

from envoy.export import EnvExporter, SUPPORTED_FORMATS
from envoy.parser import EnvParser


def register_export_subcommands(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("export", help="Export env vars to a target format")
    p.add_argument("file", help="Path to the .env file")
    p.add_argument(
        "--format",
        "-f",
        choices=SUPPORTED_FORMATS,
        default="shell",
        help="Output format (default: shell)",
    )
    p.add_argument(
        "--output",
        "-o",
        default=None,
        help="Write output to file instead of stdout",
    )


def handle_export_command(args: argparse.Namespace, out=sys.stdout) -> int:
    if not hasattr(args, "file"):
        out.write("Usage: envoy export <file> [--format FORMAT]\n")
        return 1

    try:
        with open(args.file, "r") as fh:
            raw = fh.read()
    except FileNotFoundError:
        out.write(f"Error: file not found: {args.file}\n")
        return 1

    parser = EnvParser()
    vars_ = parser.parse(raw)

    exporter = EnvExporter()
    try:
        result = exporter.export(vars_, args.format)
    except ValueError as exc:
        out.write(f"Error: {exc}\n")
        return 1

    rendered = result.render()

    if args.output:
        with open(args.output, "w") as fh:
            fh.write(rendered + "\n")
        out.write(f"Exported {len(vars_)} variable(s) to {args.output}\n")
    else:
        out.write(rendered + "\n")

    return 0
