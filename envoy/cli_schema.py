"""CLI subcommands for schema validation."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from envoy.env_schema import EnvSchema
from envoy.parser import EnvParser


def register_schema_subcommands(subparsers: Any) -> None:
    schema_parser = subparsers.add_parser("schema", help="Validate .env against a schema")
    sub = schema_parser.add_subparsers(dest="schema_cmd")

    validate_p = sub.add_parser("validate", help="Validate an env file against a JSON schema")
    validate_p.add_argument("env_file", help="Path to the .env file")
    validate_p.add_argument("schema_file", help="Path to the JSON schema file")
    validate_p.add_argument("--strict", action="store_true", help="Treat warnings as errors")


def handle_schema_command(args: Any, out=print) -> int:
    if not hasattr(args, "schema_cmd") or args.schema_cmd is None:
        out("Usage: envoy schema <subcommand>  (validate)")
        return 1

    if args.schema_cmd == "validate":
        return _validate(args, out)

    out(f"Unknown schema subcommand: {args.schema_cmd}")
    return 1


def _validate(args: Any, out) -> int:
    env_path = Path(args.env_file)
    schema_path = Path(args.schema_file)

    if not env_path.exists():
        out(f"Error: env file not found: {env_path}")
        return 1
    if not schema_path.exists():
        out(f"Error: schema file not found: {schema_path}")
        return 1

    try:
        raw_schema = json.loads(schema_path.read_text())
    except json.JSONDecodeError as exc:
        out(f"Error: invalid JSON in schema file: {exc}")
        return 1

    parser = EnvParser()
    vars_ = parser.parse(env_path.read_text())
    schema = EnvSchema.from_dict(raw_schema)
    result = schema.validate(vars_)

    for error in result.errors:
        out(f"  ERROR   {error}")
    for warning in result.warnings:
        out(f"  WARNING {warning}")

    strict_fail = args.strict and result.warnings
    if result.is_valid and not strict_fail:
        out(f"Schema validation passed ({env_path.name})")
        return 0

    if not result.is_valid:
        out(f"Schema validation FAILED — {len(result.errors)} error(s)")
    elif strict_fail:
        out(f"Schema validation FAILED (strict) — {len(result.warnings)} warning(s)")
    return 1
