import json
from typing import Any

from envoy.env_typecheck import EnvTypeChecker
from envoy.parser import EnvParser


def register_typecheck_subcommands(subparsers: Any) -> None:
    p = subparsers.add_parser("typecheck", help="Validate variable types against a schema")
    sub = p.add_subparsers(dest="typecheck_cmd")

    chk = sub.add_parser("check", help="Check env file against a type schema")
    chk.add_argument("file", help="Path to .env file")
    chk.add_argument("--schema", required=True, help="JSON file mapping keys to types")
    chk.add_argument("--strict", action="store_true", help="Exit non-zero if any violations found")


def handle_typecheck_command(args: Any, out=None) -> int:
    import sys

    if out is None:
        out = sys.stdout

    cmd = getattr(args, "typecheck_cmd", None)
    if cmd is None:
        out.write("Usage: envoy typecheck <check>\n")
        return 0

    if cmd == "check":
        return _run_check(args, out)

    out.write(f"Unknown typecheck command: {cmd}\n")
    return 1


def _run_check(args: Any, out) -> int:
    import os

    if not os.path.exists(args.file):
        out.write(f"Error: file not found: {args.file}\n")
        return 1

    if not os.path.exists(args.schema):
        out.write(f"Error: schema file not found: {args.schema}\n")
        return 1

    with open(args.file) as f:
        content = f.read()
    with open(args.schema) as f:
        schema = json.load(f)

    parser = EnvParser()
    vars = parser.parse(content)
    checker = EnvTypeChecker(schema)
    result = checker.check(vars)

    out.write(f"Checked {result.checked} variable(s).\n")
    if result.is_clean:
        out.write("All type checks passed.\n")
        return 0

    out.write(f"{len(result.violations)} violation(s) found:\n")
    for v in result.violations:
        out.write(f"  {v.key}: {v.reason}\n")

    return 1 if getattr(args, "strict", False) else 0
