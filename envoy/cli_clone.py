"""CLI subcommands for env-clone: clone an .env file with key transformations."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from envoy.env_clone import EnvCloner
from envoy.parser import EnvParser


def register_clone_subcommands(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("clone", help="Clone an .env file with key transformations")
    sub = p.add_subparsers(dest="clone_cmd")

    run_p = sub.add_parser("run", help="Perform the clone")
    run_p.add_argument("file", help="Source .env file")
    run_p.add_argument("--output", "-o", help="Destination file (default: stdout)")
    run_p.add_argument("--strip-prefix", default="", metavar="PREFIX",
                       help="Strip this prefix from all keys before cloning")
    run_p.add_argument("--add-prefix", default="", metavar="PREFIX",
                       help="Add this prefix to all keys after cloning")
    run_p.add_argument("--rename", nargs="+", metavar="OLD=NEW",
                       help="Rename keys: OLD=NEW pairs")
    run_p.add_argument("--skip", nargs="+", metavar="KEY",
                       help="Keys to skip during cloning")


def handle_clone_command(args: argparse.Namespace, out=print) -> Optional[int]:
    clone_cmd = getattr(args, "clone_cmd", None)
    if clone_cmd is None:
        out("Usage: envoy clone <subcommand> [options]")
        out("Subcommands: run")
        return 0

    if clone_cmd == "run":
        return _run_clone(args, out)

    out(f"Unknown clone subcommand: {clone_cmd}")
    return 1


def _run_clone(args: argparse.Namespace, out) -> int:
    src = Path(args.file)
    if not src.exists():
        out(f"Error: file not found: {src}")
        return 1

    raw = src.read_text(encoding="utf-8")
    parser = EnvParser()
    vars = parser.parse(raw)

    rename_map: dict = {}
    for pair in (args.rename or []):
        if "=" not in pair:
            out(f"Error: invalid rename spec '{pair}' (expected OLD=NEW)")
            return 1
        old, new = pair.split("=", 1)
        rename_map[old.strip()] = new.strip()

    cloner = EnvCloner(
        strip_prefix=args.strip_prefix,
        add_prefix=args.add_prefix,
        rename_map=rename_map,
        skip_keys=args.skip or [],
    )
    result = cloner.clone(vars)

    serialized = parser.serialize(result.cloned)

    if args.output:
        Path(args.output).write_text(serialized, encoding="utf-8")
        out(f"Cloned {len(result.cloned)} vars to {args.output}")
        if result.skipped:
            out(f"Skipped: {', '.join(result.skipped)}")
        if result.renamed:
            for old, new in result.renamed.items():
                out(f"  Renamed: {old} -> {new}")
    else:
        out(serialized)

    return 0
