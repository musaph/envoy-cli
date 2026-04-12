"""CLI subcommands for env-chain (multi-file precedence merging)."""
from __future__ import annotations
import argparse
from pathlib import Path
from typing import Callable

from envoy.env_chain import EnvChainer
from envoy.parser import EnvParser


def register_chain_subcommands(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("chain", help="Merge multiple .env files with override precedence")
    chain_sub = p.add_subparsers(dest="chain_cmd")

    merge_p = chain_sub.add_parser("merge", help="Merge files left-to-right (later overrides earlier)")
    merge_p.add_argument("files", nargs="+", metavar="FILE", help=".env files in precedence order")
    merge_p.add_argument("--show-overrides", action="store_true", help="Print keys that were overridden")


def handle_chain_command(args: argparse.Namespace, out: Callable[[str], None] = print) -> int:
    if not hasattr(args, "chain_cmd") or args.chain_cmd is None:
        out("Usage: envoy chain <subcommand>  (merge)")
        return 1

    if args.chain_cmd == "merge":
        return _run_merge(args, out)

    out(f"Unknown chain subcommand: {args.chain_cmd}")
    return 1


def _run_merge(args: argparse.Namespace, out: Callable[[str], None]) -> int:
    parser = EnvParser()
    chainer = EnvChainer()
    sources = []

    for filepath in args.files:
        p = Path(filepath)
        if not p.exists():
            out(f"Error: file not found: {filepath}")
            return 1
        text = p.read_text(encoding="utf-8")
        vars_dict = parser.parse(text)
        sources.append((filepath, vars_dict))

    result = chainer.chain(sources)

    out(f"Merged {len(result.merged)} keys from {len(result.sources)} source(s).")

    if getattr(args, "show_overrides", False) and result.overridden_entries:
        out("\nOverridden keys:")
        for entry in result.overridden_entries:
            out(f"  {entry.key}: [{entry.source}] -> overridden by [{entry.overridden_by}]")

    out("\nFinal values:")
    for key, value in sorted(result.merged.items()):
        out(f"  {key}={value}")

    return 0
