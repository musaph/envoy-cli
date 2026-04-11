"""CLI subcommands for the env-watch feature."""
from __future__ import annotations

import argparse
import sys
from typing import Any

from envoy.env_watch import EnvWatcher, WatchEvent


def register_watch_subcommands(subparsers: Any) -> None:
    p: argparse.ArgumentParser = subparsers.add_parser(
        "watch",
        help="Watch .env files for changes and print events",
    )
    p.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="One or more .env files to watch",
    )
    p.add_argument(
        "--interval",
        type=float,
        default=1.0,
        metavar="SECS",
        help="Polling interval in seconds (default: 1.0)",
    )
    p.add_argument(
        "--once",
        action="store_true",
        help="Poll once and exit (useful for scripting / tests)",
    )


def handle_watch_command(args: Any, out=sys.stdout) -> int:
    if not hasattr(args, "files"):
        out.write("Usage: envoy watch <file> [file ...]\n")
        return 1

    watcher = EnvWatcher(paths=args.files, interval=getattr(args, "interval", 1.0))

    def _print_event(evt: WatchEvent) -> None:
        tag = {"modified": "~", "created": "+", "deleted": "-"}.get(evt.kind, "?")
        out.write(f"[{tag}] {evt.kind.upper():8s}  {evt.path}\n")

    watcher.on_change(_print_event)

    once = getattr(args, "once", False)
    if once:
        events = watcher.poll()
        if not events:
            out.write("No changes detected.\n")
        return 0

    out.write(f"Watching {len(args.files)} file(s) — press Ctrl+C to stop.\n")
    try:
        watcher.watch()
    except KeyboardInterrupt:
        out.write("\nStopped.\n")
    return 0
