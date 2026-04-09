"""CLI subcommands for lockfile management.

Exposes:
  envoy lock generate  – create / refresh .envoy-lock.json from current env file
  envoy lock check     – verify env file has not drifted from the lock
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable

from envoy.lockfile import Lockfile
from envoy.parser import EnvParser


def register_lock_subcommands(subparsers: argparse.Action) -> None:  # type: ignore[type-arg]
    lock_parser = subparsers.add_parser("lock", help="Manage the envoy lockfile")
    lock_sub = lock_parser.add_subparsers(dest="lock_command")

    gen = lock_sub.add_parser("generate", help="Generate or refresh the lockfile")
    gen.add_argument("--env-file", default=".env", help="Path to the .env file")
    gen.add_argument("--profile", default="default", help="Profile name to embed")
    gen.add_argument("--dir", default=".", help="Directory to write the lockfile into")

    chk = lock_sub.add_parser("check", help="Check env file against the lockfile")
    chk.add_argument("--env-file", default=".env", help="Path to the .env file")
    chk.add_argument("--dir", default=".", help="Directory containing the lockfile")


def handle_lock_command(
    args: argparse.Namespace,
    out: Callable[[str], None] = print,
) -> int:
    """Dispatch lock sub-commands.  Returns an exit code (0 = success)."""
    cmd = getattr(args, "lock_command", None)

    if cmd == "generate":
        return _generate(args, out)
    if cmd == "check":
        return _check(args, out)

    out("Usage: envoy lock <generate|check>")
    return 1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_vars(env_file: str, out: Callable[[str], None]) -> dict | None:
    path = Path(env_file)
    if not path.exists():
        out(f"Error: env file not found: {env_file}")
        return None
    return EnvParser.parse(path.read_text())


def _generate(args: argparse.Namespace, out: Callable[[str], None]) -> int:
    variables = _load_vars(args.env_file, out)
    if variables is None:
        return 1

    directory = Path(args.dir)
    directory.mkdir(parents=True, exist_ok=True)

    lf = Lockfile.load(directory) or Lockfile(profile=args.profile)
    lf.profile = args.profile
    lf.update(variables)
    saved = lf.save(directory)
    out(f"Lockfile written to {saved} ({len(variables)} keys, profile={args.profile})")
    return 0


def _check(args: argparse.Namespace, out: Callable[[str], None]) -> int:
    variables = _load_vars(args.env_file, out)
    if variables is None:
        return 1

    directory = Path(args.dir)
    lf = Lockfile.load(directory)
    if lf is None:
        out("Error: no lockfile found. Run 'envoy lock generate' first.")
        return 1

    if lf.is_stale(variables):
        out("Drift detected: env file does not match the lockfile.")
        out("Run 'envoy lock generate' to update the lockfile.")
        return 2

    out(f"OK: env file matches lockfile (profile={lf.profile}, {len(variables)} keys).")
    return 0
