"""CLI subcommands for env-tokenize."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from envoy.env_tokenize import EnvTokenizer
from envoy.parser import EnvParser


def register_tokenize_subcommands(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("tokenize", help="Tokenize env var values into parts")
    p.add_argument("file", help="Path to .env file")
    p.add_argument("--pattern", default=None, help="Regex delimiter pattern")
    p.add_argument("--keys", nargs="+", default=None, help="Restrict to these keys")
    p.add_argument(
        "--min-tokens",
        type=int,
        default=2,
        dest="min_tokens",
        help="Minimum tokens required to include a key (default: 2)",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )


def handle_tokenize_command(args: argparse.Namespace, out=sys.stdout) -> int:
    if not hasattr(args, "file"):
        out.write("Usage: envoy tokenize <file> [options]\n")
        return 1

    path = Path(args.file)
    if not path.exists():
        out.write(f"Error: file not found: {args.file}\n")
        return 1

    raw = path.read_text(encoding="utf-8")
    parser = EnvParser()
    vars_ = parser.parse(raw)

    tokenizer = EnvTokenizer(
        pattern=getattr(args, "pattern", None),
        keys=getattr(args, "keys", None),
        min_tokens=getattr(args, "min_tokens", 2),
    )
    result = tokenizer.tokenize(vars_)

    fmt = getattr(args, "format", "text")
    if fmt == "json":
        out.write(json.dumps(tokenizer.as_dict(result), indent=2) + "\n")
    else:
        if not result.has_changes():
            out.write("No keys produced multiple tokens.\n")
        for change in result.changes:
            out.write(f"{change.key}: {' | '.join(change.tokens)}\n")
        if result.skipped:
            out.write(f"Skipped (too few tokens): {', '.join(result.skipped)}\n")

    return 0
