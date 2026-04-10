"""CLI subcommands for env var type casting."""
import json
from typing import Any

from envoy.env_cast import EnvCaster
from envoy.parser import EnvParser


def register_cast_subcommands(subparsers: Any) -> None:
    cast_parser = subparsers.add_parser("cast", help="Inspect and cast .env variable types")
    cast_sub = cast_parser.add_subparsers(dest="cast_cmd")

    inspect = cast_sub.add_parser("inspect", help="Show inferred types for all variables")
    inspect.add_argument("file", help="Path to .env file")
    inspect.add_argument("--format", choices=["table", "json"], default="table")

    preview = cast_sub.add_parser("preview", help="Preview casted Python values")
    preview.add_argument("file", help="Path to .env file")
    preview.add_argument("--hints", nargs="*", metavar="KEY=TYPE",
                         help="Type hints e.g. PORT=int DEBUG=bool")


def handle_cast_command(args: Any, out=None) -> int:
    import sys
    out = out or sys.stdout

    cmd = getattr(args, "cast_cmd", None)
    if cmd is None:
        out.write("Usage: envoy cast {inspect,preview}\n")
        return 1

    try:
        with open(args.file) as f:
            content = f.read()
    except FileNotFoundError:
        out.write(f"Error: file not found: {args.file}\n")
        return 1

    parser = EnvParser()
    caster = EnvCaster()
    vars_dict = parser.parse(content)

    if cmd == "inspect":
        results = caster.cast_all(vars_dict)
        if getattr(args, "format", "table") == "json":
            data = [
                {"key": r.key, "raw": r.raw, "type": r.cast_type, "success": r.success}
                for r in results
            ]
            out.write(json.dumps(data, indent=2) + "\n")
        else:
            out.write(f"{'KEY':<30} {'TYPE':<10} {'RAW VALUE':<30}\n")
            out.write("-" * 72 + "\n")
            for r in results:
                status = r.cast_type if r.success else f"error"
                out.write(f"{r.key:<30} {status:<10} {r.raw:<30}\n")
        return 0

    if cmd == "preview":
        hints: dict = {}
        raw_hints = getattr(args, "hints", None) or []
        for item in raw_hints:
            if "=" in item:
                k, t = item.split("=", 1)
                hints[k.strip()] = t.strip()
        results = caster.cast_all(vars_dict, hints=hints)
        out.write(f"{'KEY':<30} {'TYPE':<10} {'PYTHON VALUE'}\n")
        out.write("-" * 72 + "\n")
        for r in results:
            out.write(f"{r.key:<30} {r.cast_type:<10} {r.r}\n")
        return 0

    out.write(f"Unknown cast subcommand: {cmd}\n")
    return 1
