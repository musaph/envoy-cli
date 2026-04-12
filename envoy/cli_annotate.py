"""CLI subcommands for env-variable annotation."""
from __future__ import annotations
from typing import Callable
from envoy.env_annotate import EnvAnnotator
from envoy.parser import EnvParser


def register_annotate_subcommands(subparsers) -> None:
    p = subparsers.add_parser("annotate", help="Annotate .env variables with comments/tags")
    sub = p.add_subparsers(dest="annotate_cmd")

    add_p = sub.add_parser("add", help="Add an annotation to a key")
    add_p.add_argument("file", help="Path to .env file")
    add_p.add_argument("key", help="Variable key to annotate")
    add_p.add_argument("comment", help="Comment text")
    add_p.add_argument("--tags", nargs="*", default=[], help="Optional tags")

    show_p = sub.add_parser("show", help="Show annotations for a .env file")
    show_p.add_argument("file", help="Path to .env file")


def handle_annotate_command(args, output: Callable[[str], None] = print) -> int:
    if not hasattr(args, "annotate_cmd") or args.annotate_cmd is None:
        output("Usage: envoy annotate <add|show> [options]")
        return 1

    parser = EnvParser()
    annotator = EnvAnnotator()

    try:
        with open(args.file) as fh:
            raw = fh.read()
    except FileNotFoundError:
        output(f"Error: file not found: {args.file}")
        return 2

    vars_ = parser.parse(raw)

    if args.annotate_cmd == "add":
        if args.key not in vars_:
            output(f"Warning: key '{args.key}' not found in {args.file}")
        ann = annotator.annotate(args.key, args.comment, args.tags)
        output(f"Annotated: {ann}")
        return 0

    if args.annotate_cmd == "show":
        result = annotator.apply(vars_)
        if not result.annotated:
            output("No annotations found.")
        for key, ann in result.annotated.items():
            tag_str = ", ".join(ann.tags) if ann.tags else "(none)"
            output(f"  {key}: {ann.comment} [tags: {tag_str}]")
        return 0

    output(f"Unknown subcommand: {args.annotate_cmd}")
    return 1
