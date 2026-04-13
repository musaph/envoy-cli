"""CLI subcommands for sensitive key classification."""
from typing import Any

from envoy.env_sensitive import EnvSensitiveClassifier
from envoy.parser import EnvParser


def register_sensitive_subcommands(subparsers: Any) -> None:
    p = subparsers.add_parser("sensitive", help="Classify sensitive env vars")
    sub = p.add_subparsers(dest="sensitive_cmd")

    scan = sub.add_parser("scan", help="Scan a .env file for sensitive keys")
    scan.add_argument("file", help="Path to .env file")
    scan.add_argument("--min-confidence", choices=["low", "medium", "high"], default="low")


def handle_sensitive_command(args: Any, out=print) -> int:
    if not hasattr(args, "sensitive_cmd") or args.sensitive_cmd is None:
        out("Usage: envoy sensitive <scan>")
        return 1

    if args.sensitive_cmd == "scan":
        return _run_scan(args, out)

    out(f"Unknown subcommand: {args.sensitive_cmd}")
    return 1


_CONFIDENCE_ORDER = {"low": 0, "medium": 1, "high": 2}


def _run_scan(args: Any, out=print) -> int:
    try:
        with open(args.file) as fh:
            raw = fh.read()
    except FileNotFoundError:
        out(f"Error: file not found: {args.file}")
        return 1

    parser = EnvParser()
    vars_ = parser.parse(raw)
    classifier = EnvSensitiveClassifier()
    result = classifier.classify(vars_)

    min_level = _CONFIDENCE_ORDER[args.min_confidence]
    filtered = [e for e in result.entries if _CONFIDENCE_ORDER[e.confidence] >= min_level]

    if not filtered:
        out(f"No sensitive keys found (scanned {result.scanned} vars).")
        return 0

    out(f"Sensitive keys found ({len(filtered)}/{result.scanned} vars):")
    for entry in filtered:
        out(f"  [{entry.confidence.upper()}] {entry.key}  (category: {entry.category})")
    return 0
