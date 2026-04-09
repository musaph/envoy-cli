"""CLI subcommands for secret scanning within envoy-cli."""

from typing import List
from envoy.secrets import SecretScanner
from envoy.env_file import EnvFile
from envoy.parser import EnvParser


def register_secrets_subcommands(subparsers):
    """Attach 'secrets' subparser to the main CLI argument parser."""
    secrets_parser = subparsers.add_parser(
        "secrets",
        help="Scan .env files for potentially sensitive values",
    )
    secrets_sub = secrets_parser.add_subparsers(dest="secrets_cmd")

    scan_p = secrets_sub.add_parser("scan", help="List sensitive keys in a file")
    scan_p.add_argument("file", nargs="?", default=".env", help="Path to .env file")
    scan_p.add_argument("--extra-patterns", nargs="*", default=[], metavar="PATTERN")

    mask_p = secrets_sub.add_parser("mask", help="Print .env with sensitive values masked")
    mask_p.add_argument("file", nargs="?", default=".env", help="Path to .env file")


def handle_secrets_command(args, output: List[str]):
    """Dispatch secrets subcommands."""
    cmd = getattr(args, "secrets_cmd", None)
    if cmd is None:
        output.append("Usage: envoy secrets {scan,mask}")
        return

    env_file = EnvFile(getattr(args, "file", ".env"))
    if not env_file.exists():
        output.append(f"Error: file '{args.file}' not found.")
        return

    raw = env_file.read()
    variables = EnvParser.parse(raw)

    if cmd == "scan":
        extra = getattr(args, "extra_patterns", [])
        scanner = SecretScanner(extra_key_patterns=extra or None)
        matches = scanner.scan(variables)
        if not matches:
            output.append("No sensitive variables detected.")
        else:
            output.append(f"Found {len(matches)} sensitive variable(s):")
            for m in matches:
                output.append(f"  {m.key}  [{m.reason}]  preview: {m.value_preview}")

    elif cmd == "mask":
        scanner = SecretScanner()
        masked = scanner.mask(variables)
        output.append(EnvParser.serialize(masked))
