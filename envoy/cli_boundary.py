"""CLI subcommands for env boundary checking."""
from __future__ import annotations

import json
from typing import Any

from envoy.env_boundary import BoundaryRule, EnvBoundaryChecker


def register_boundary_subcommands(subparsers: Any) -> None:
    p = subparsers.add_parser("boundary", help="Check env var value boundaries")
    sub = p.add_subparsers(dest="boundary_cmd")

    chk = sub.add_parser("check", help="Check values against boundary rules")
    chk.add_argument("file", help="Path to .env file")
    chk.add_argument(
        "--rules",
        required=True,
        help="JSON file defining boundary rules per key",
    )


def handle_boundary_command(args: Any, out=print) -> int:
    if not hasattr(args, "boundary_cmd") or args.boundary_cmd is None:
        out("Usage: envoy boundary <check>")
        return 1
    if args.boundary_cmd == "check":
        return _run_check(args, out)
    out(f"Unknown boundary subcommand: {args.boundary_cmd}")
    return 1


def _run_check(args: Any, out) -> int:
    import pathlib

    env_path = pathlib.Path(args.file)
    if not env_path.exists():
        out(f"Error: env file not found: {args.file}")
        return 1

    rules_path = pathlib.Path(args.rules)
    if not rules_path.exists():
        out(f"Error: rules file not found: {args.rules}")
        return 1

    try:
        raw_rules = json.loads(rules_path.read_text())
    except json.JSONDecodeError as exc:
        out(f"Error: invalid JSON in rules file: {exc}")
        return 1

    from envoy.parser import EnvParser

    vars_ = EnvParser.parse(env_path.read_text())
    checker = EnvBoundaryChecker()
    for key, rule_dict in raw_rules.items():
        checker.add_rule(
            key,
            BoundaryRule(
                min_length=rule_dict.get("min_length"),
                max_length=rule_dict.get("max_length"),
                min_value=rule_dict.get("min_value"),
                max_value=rule_dict.get("max_value"),
            ),
        )

    result = checker.check(vars_)
    if result.is_clean:
        out("All boundary checks passed.")
        return 0

    out(f"Boundary violations found ({len(result.violations)}):")
    for v in result.violations:
        out(f"  {v.key}: {v.reason}")
    return 1
