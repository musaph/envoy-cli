"""CLI subcommands for env variable expiry checking."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from envoy.env_expire import EnvExpiryChecker, ExpiryEntry
from envoy.parser import EnvParser


def register_expire_subcommands(subparsers: Any) -> None:
    p = subparsers.add_parser("expire", help="Check env variable expiry dates")
    sub = p.add_subparsers(dest="expire_cmd")

    chk = sub.add_parser("check", help="Check a .env file against an expiry manifest")
    chk.add_argument("file", help="Path to .env file")
    chk.add_argument("manifest", help="Path to JSON expiry manifest")


def handle_expire_command(args: Any, out=print) -> int:
    if not hasattr(args, "expire_cmd") or args.expire_cmd is None:
        out("Usage: envoy expire <check>")
        return 1

    if args.expire_cmd == "check":
        return _run_check(args, out)

    out(f"Unknown expire subcommand: {args.expire_cmd}")
    return 1


def _run_check(args: Any, out) -> int:
    try:
        raw = open(args.file).read()
    except FileNotFoundError:
        out(f"Error: file not found: {args.file}")
        return 1

    try:
        manifest_data = json.loads(open(args.manifest).read())
    except FileNotFoundError:
        out(f"Error: manifest not found: {args.manifest}")
        return 1
    except json.JSONDecodeError as exc:
        out(f"Error: invalid JSON manifest: {exc}")
        return 1

    parser = EnvParser()
    vars_ = parser.parse(raw)

    entries = [ExpiryEntry.from_dict(d) for d in manifest_data.get("entries", [])]
    checker = EnvExpiryChecker(entries)
    result = checker.check(vars_, now=datetime.now(timezone.utc))

    if not result.has_violations:
        out(f"All {result.checked} tracked variable(s) are current.")
        return 0

    for v in result.expired:
        out(f"[EXPIRED]  {v.key} expired on {v.expires_at.date()}")
    for v in result.expiring_soon:
        out(f"[SOON]     {v.key} expires on {v.expires_at.date()}")

    return 1
