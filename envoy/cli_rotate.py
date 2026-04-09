"""CLI subcommands for key rotation."""
import getpass
from typing import Any

from envoy.rotate import KeyRotator


def register_rotate_subcommands(subparsers: Any) -> None:
    rotate_parser = subparsers.add_parser(
        "rotate", help="Re-encrypt stored env vars with a new password"
    )
    rotate_parser.add_argument(
        "--env", required=True, help="Environment name (e.g. production)"
    )
    rotate_parser.add_argument(
        "--storage-path", required=True, help="Path to the local storage directory"
    )
    rotate_parser.add_argument(
        "--initiated-by", default="cli", help="Who initiated the rotation"
    )


def handle_rotate_command(args: Any, out=print) -> int:
    """Handle the rotate subcommand. Returns exit code."""
    if not hasattr(args, "env") or args.env is None:
        out("Usage: envoy rotate --env <name> --storage-path <path>")
        return 1

    import json
    import os

    storage_path = args.storage_path
    env = args.env
    blob_file = os.path.join(storage_path, f"{env}.json")

    if not os.path.exists(blob_file):
        out(f"Error: no stored data found for environment '{env}'.")
        return 1

    old_password = getpass.getpass("Current password: ")
    new_password = getpass.getpass("New password: ")
    confirm = getpass.getpass("Confirm new password: ")

    if new_password != confirm:
        out("Error: new passwords do not match.")
        return 1

    try:
        rotator = KeyRotator(old_password, new_password)
    except ValueError as exc:
        out(f"Error: {exc}")
        return 1

    with open(blob_file, "r") as fh:
        blobs: dict = json.load(fh)

    try:
        rotated = rotator.rotate_all(blobs)
    except Exception as exc:
        out(f"Error during rotation: {exc}")
        return 1

    with open(blob_file, "w") as fh:
        json.dump(rotated, fh, indent=2)

    record = rotator.build_record(
        environment=env,
        keys_affected=len(rotated),
        initiated_by=getattr(args, "initiated_by", "cli"),
    )
    out(f"Rotation complete. {record.keys_affected} key(s) re-encrypted for '{env}'.")
    out(f"Rotated at: {record.rotated_at}")
    return 0
