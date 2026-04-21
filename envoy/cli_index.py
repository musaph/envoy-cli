"""CLI subcommands for env-index: build and query a key index."""
from __future__ import annotations
import json
from typing import Any

from envoy.env_index import EnvIndexer
from envoy.parser import EnvParser


def register_index_subcommands(subparsers: Any) -> None:
    p = subparsers.add_parser("index", help="Build and query an index of env keys")
    sub = p.add_subparsers(dest="index_cmd")

    build = sub.add_parser("build", help="Print index of all keys")
    build.add_argument("file", help="Path to .env file")
    build.add_argument("--prefix", help="Filter by prefix", default=None)
    build.add_argument("--json", dest="as_json", action="store_true", help="Output as JSON")

    empty = sub.add_parser("empty", help="List keys with empty values")
    empty.add_argument("file", help="Path to .env file")


def handle_index_command(args: Any, out=None) -> int:
    import sys
    out = out or sys.stdout

    if not hasattr(args, "index_cmd") or args.index_cmd is None:
        out.write("Usage: envoy index <build|empty>\n")
        return 1

    try:
        content = open(args.file).read()
    except FileNotFoundError:
        out.write(f"Error: file not found: {args.file}\n")
        return 2

    parser = EnvParser()
    vars_ = parser.parse(content)
    indexer = EnvIndexer()
    result = indexer.build(vars_)

    if args.index_cmd == "build":
        entries = result.by_prefix(args.prefix) if args.prefix else result.entries
        if getattr(args, "as_json", False):
            out.write(json.dumps([e.to_dict() for e in entries], indent=2) + "\n")
        else:
            for e in entries:
                flag = " [empty]" if e.is_empty else ""
                out.write(f"{e.position:>4}  {e.key}  (prefix={e.prefix}){flag}\n")
        return 0

    if args.index_cmd == "empty":
        empty_keys = result.empty_keys
        if not empty_keys:
            out.write("No empty values found.\n")
        else:
            for k in empty_keys:
                out.write(f"{k}\n")
        return 0

    out.write(f"Unknown index subcommand: {args.index_cmd}\n")
    return 1
