from __future__ import annotations
import argparse
from typing import Any

from envoy.env_search import EnvSearch
from envoy.parser import EnvParser


def register_search_subcommands(subparsers: Any) -> None:
    p = subparsers.add_parser("search", help="Search variables in a .env file")
    sub = p.add_subparsers(dest="search_cmd")

    run = sub.add_parser("run", help="Search for a query in keys and/or values")
    run.add_argument("file", help="Path to .env file")
    run.add_argument("query", help="Search query (substring or regex)")
    run.add_argument("--keys-only", action="store_true", help="Search keys only")
    run.add_argument("--case-sensitive", action="store_true", help="Case-sensitive search")

    prefix_cmd = sub.add_parser("prefix", help="Filter vars by key prefix")
    prefix_cmd.add_argument("file", help="Path to .env file")
    prefix_cmd.add_argument("prefix", help="Key prefix to filter by")


def handle_search_command(args: Any, out=print) -> int:
    search_cmd = getattr(args, "search_cmd", None)
    if search_cmd is None:
        out("Usage: envoy search <run|prefix> [options]")
        return 1

    try:
        with open(args.file, "r") as fh:
            content = fh.read()
    except FileNotFoundError:
        out(f"Error: file not found: {args.file}")
        return 1

    vars_ = EnvParser.parse(content)

    if search_cmd == "run":
        search_values = not getattr(args, "keys_only", False)
        searcher = EnvSearch(
            case_sensitive=getattr(args, "case_sensitive", False),
            search_values=search_values,
        )
        result = searcher.search(vars_, args.query)
        if not result.found:
            out(f"No matches for '{args.query}'.")
            return 0
        out(f"Found {len(result.matches)} match(es) for '{args.query}':")
        for m in result.matches:
            out(f"  [{m.match_on}] {m.key}={m.value}")
        return 0

    if search_cmd == "prefix":
        searcher = EnvSearch(case_sensitive=getattr(args, "case_sensitive", False))
        filtered = searcher.filter_by_prefix(vars_, args.prefix)
        if not filtered:
            out(f"No variables with prefix '{args.prefix}'.")
            return 0
        out(f"Variables with prefix '{args.prefix}':")
        for k, v in filtered.items():
            out(f"  {k}={v}")
        return 0

    out(f"Unknown search subcommand: {search_cmd}")
    return 1
