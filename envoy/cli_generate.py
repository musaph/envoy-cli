"""CLI subcommands for env-generate: scaffold .env files from field specs."""
import json
from typing import List

from envoy.env_generate import EnvGenerator, GenerateField
from envoy.parser import EnvParser


def register_generate_subcommands(subparsers):
    p = subparsers.add_parser("generate", help="Generate a .env file from a spec")
    sub = p.add_subparsers(dest="generate_cmd")

    run_p = sub.add_parser("run", help="Generate env vars from a JSON spec file")
    run_p.add_argument("spec", help="Path to JSON spec file")
    run_p.add_argument("--out", help="Output .env file path (default: stdout)")
    run_p.add_argument("--length", type=int, default=32, help="Length for auto-generated secrets")


def handle_generate_command(args, out=None):
    import sys
    out = out or sys.stdout

    generate_cmd = getattr(args, "generate_cmd", None)
    if generate_cmd is None:
        out.write("Usage: envoy generate <subcommand>\n")
        return 1

    if generate_cmd == "run":
        return _run_generate(args, out)

    out.write(f"Unknown generate subcommand: {generate_cmd}\n")
    return 1


def _run_generate(args, out):
    try:
        with open(args.spec) as fh:
            raw = json.load(fh)
    except FileNotFoundError:
        out.write(f"Error: spec file not found: {args.spec}\n")
        return 1
    except json.JSONDecodeError as exc:
        out.write(f"Error: invalid JSON in spec: {exc}\n")
        return 1

    fields: List[GenerateField] = []
    for item in raw.get("fields", []):
        fields.append(GenerateField(
            key=item["key"],
            default=item.get("default"),
            auto=item.get("auto"),
            required=item.get("required", False),
        ))

    generator = EnvGenerator(length=getattr(args, "length", 32))
    result = generator.generate(fields)

    if result.has_errors:
        for err in result.errors:
            out.write(f"Error: {err}\n")
        return 1

    parser = EnvParser()
    content = parser.serialize(result.generated)

    output_path = getattr(args, "out", None)
    if output_path:
        with open(output_path, "w") as fh:
            fh.write(content)
        out.write(f"Generated {len(result.generated)} variable(s) -> {output_path}\n")
        if result.skipped:
            out.write(f"Skipped (no value/default): {', '.join(result.skipped)}\n")
    else:
        out.write(content)

    return 0
