"""CLI subcommands for env freeze/check operations."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from envoy.env_freeze import EnvFreezer, FreezeResult
from envoy.parser import EnvParser


def register_freeze_subcommands(subparsers: Any) -> None:
    freeze_p = subparsers.add_parser("freeze", help="Freeze and verify .env files")
    freeze_sub = freeze_p.add_subparsers(dest="freeze_cmd")

    snap = freeze_sub.add_parser("snap", help="Snapshot current .env into a freeze file")
    snap.add_argument("file", help="Path to .env file")
    snap.add_argument("--output", "-o", default=".envfreeze", help="Output freeze file")

    chk = freeze_sub.add_parser("check", help="Check .env against a freeze file")
    chk.add_argument("file", help="Path to .env file")
    chk.add_argument("--freeze-file", default=".envfreeze", help="Freeze file to compare against")


def handle_freeze_command(args: Any, out=print) -> int:
    cmd = getattr(args, "freeze_cmd", None)
    if cmd is None:
        out("Usage: envoy freeze <snap|check>")
        return 1

    parser = EnvParser()
    freezer = EnvFreezer()

    if cmd == "snap":
        env_path = Path(args.file)
        if not env_path.exists():
            out(f"Error: file not found: {args.file}")
            return 1
        vars_ = parser.parse(env_path.read_text())
        result = freezer.freeze(vars_)
        output_path = Path(args.output)
        output_path.write_text(json.dumps(result.to_dict(), indent=2))
        out(f"Frozen {len(vars_)} variable(s) to {args.output}")
        return 0

    if cmd == "check":
        env_path = Path(args.file)
        freeze_path = Path(args.freeze_file)
        if not env_path.exists():
            out(f"Error: file not found: {args.file}")
            return 1
        if not freeze_path.exists():
            out(f"Error: freeze file not found: {args.freeze_file}")
            return 1
        current = parser.parse(env_path.read_text())
        frozen = FreezeResult.from_dict(json.loads(freeze_path.read_text()))
        result = freezer.check(frozen, current)
        if result.is_clean:
            out("OK: environment matches frozen snapshot.")
            return 0
        out(f"FAIL: {len(result.violations)} violation(s) detected:")
        for v in result.violations:
            out(f"  {v.key}: expected={v.expected!r}, actual={v.actual!r}")
        return 1

    out(f"Unknown freeze subcommand: {cmd}")
    return 1
