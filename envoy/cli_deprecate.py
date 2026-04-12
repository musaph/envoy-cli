"""CLI subcommands for deprecation checking."""
from typing import Callable, Optional

from envoy.env_deprecate import DeprecationEntry, EnvDeprecationChecker
from envoy.parser import EnvParser


def register_deprecate_subcommands(subparsers) -> None:
    p = subparsers.add_parser("deprecate", help="Check for deprecated env vars")
    sub = p.add_subparsers(dest="deprecate_cmd")

    chk = sub.add_parser("check", help="Check a .env file for deprecated keys")
    chk.add_argument("file", help="Path to .env file")
    chk.add_argument(
        "--rule",
        action="append",
        dest="rules",
        metavar="KEY:REASON[:REPLACEMENT]",
        help="Deprecation rule (repeatable)",
    )


def _parse_rule(rule_str: str) -> Optional[DeprecationEntry]:
    parts = rule_str.split(":", 2)
    if len(parts) < 2:
        return None
    key, reason = parts[0].strip(), parts[1].strip()
    replacement = parts[2].strip() if len(parts) == 3 else None
    return DeprecationEntry(key=key, reason=reason, replacement=replacement)


def handle_deprecate_command(args, out: Callable[[str], None] = print) -> int:
    if not hasattr(args, "deprecate_cmd") or args.deprecate_cmd is None:
        out("Usage: envoy deprecate <check> [options]")
        return 1

    if args.deprecate_cmd == "check":
        import os
        if not os.path.isfile(args.file):
            out(f"Error: file not found: {args.file}")
            return 2

        entries = []
        for rule_str in (args.rules or []):
            entry = _parse_rule(rule_str)
            if entry:
                entries.append(entry)
            else:
                out(f"Warning: could not parse rule {rule_str!r}, skipping")

        with open(args.file) as fh:
            content = fh.read()

        vars_ = EnvParser.parse(content)
        checker = EnvDeprecationChecker(entries)
        result = checker.check(vars_)

        if not result.has_violations:
            out("No deprecated variables found.")
            return 0

        out(f"Found {len(result.present_keys)} deprecated variable(s):")
        suggestions = checker.suggestions(vars_)
        for key in result.present_keys:
            entry = next(e for e in result.deprecated if e.key == key)
            repl = suggestions.get(key)
            msg = f"  - {key}: {entry.reason}"
            if repl:
                msg += f" (use {repl!r} instead)"
            out(msg)
        return 3

    out(f"Unknown subcommand: {args.deprecate_cmd}")
    return 1
