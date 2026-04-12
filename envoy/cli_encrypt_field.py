"""CLI subcommands for field-level encryption."""
from __future__ import annotations
import argparse
import getpass
from pathlib import Path
from envoy.parser import EnvParser
from envoy.env_encrypt_field import EnvFieldEncryptor


def register_encrypt_field_subcommands(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("encrypt-fields", help="Field-level encrypt/decrypt .env values")
    fsub = p.add_subparsers(dest="ef_cmd")

    enc = fsub.add_parser("encrypt", help="Encrypt selected fields")
    enc.add_argument("file", help="Path to .env file")
    enc.add_argument("--keys", nargs="+", metavar="KEY", help="Keys to encrypt (default: all)")
    enc.add_argument("--inplace", action="store_true", help="Overwrite the source file")

    dec = fsub.add_parser("decrypt", help="Decrypt selected fields")
    dec.add_argument("file", help="Path to .env file")
    dec.add_argument("--keys", nargs="+", metavar="KEY", help="Keys to decrypt (default: all encrypted)")
    dec.add_argument("--inplace", action="store_true", help="Overwrite the source file")


def handle_encrypt_field_command(args: argparse.Namespace, out=print) -> int:
    if not hasattr(args, "ef_cmd") or args.ef_cmd is None:
        out("Usage: envoy encrypt-fields <encrypt|decrypt> <file> [options]")
        return 1

    path = Path(args.file)
    if not path.exists():
        out(f"Error: file not found: {path}")
        return 1

    raw = path.read_text()
    vars_ = EnvParser.parse(raw)
    password = getpass.getpass("Password: ")
    encryptor = EnvFieldEncryptor(password)

    if args.ef_cmd == "encrypt":
        result = encryptor.encrypt_fields(vars_, keys=getattr(args, "keys", None))
    else:
        result = encryptor.decrypt_fields(vars_, keys=getattr(args, "keys", None))

    if result.has_errors:
        for k, msg in result.errors.items():
            out(f"Error processing '{k}': {msg}")
        return 1

    if result.skipped:
        out(f"Skipped (already in target state): {', '.join(result.skipped)}")

    serialized = EnvParser.serialize(result.encrypted)
    if getattr(args, "inplace", False):
        path.write_text(serialized)
        out(f"Written to {path}")
    else:
        out(serialized)

    return 0
