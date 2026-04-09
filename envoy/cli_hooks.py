"""CLI sub-commands for managing envoy hooks configuration."""
from __future__ import annotations

import argparse
from typing import Callable

from envoy.hooks import HookEvent


def register_hooks_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    hooks_parser = subparsers.add_parser("hooks", help="Manage lifecycle hooks")
    hooks_sub = hooks_parser.add_subparsers(dest="hooks_cmd")

    # list
    hooks_sub.add_parser("list", help="List all configured hooks")

    # add
    add_p = hooks_sub.add_parser("add", help="Register a hook command for an event")
    add_p.add_argument("event", choices=[e.value for e in HookEvent])
    add_p.add_argument("command", help="Shell command to run")

    # remove
    rm_p = hooks_sub.add_parser("remove", help="Remove a hook command from an event")
    rm_p.add_argument("event", choices=[e.value for e in HookEvent])
    rm_p.add_argument("command", help="Exact command string to remove")

    # run
    run_p = hooks_sub.add_parser("run", help="Manually trigger hooks for an event")
    run_p.add_argument("event", choices=[e.value for e in HookEvent])


def handle_hooks_command(args: argparse.Namespace, config: object, out: Callable[[str], None] = print) -> int:
    """Dispatch hooks sub-commands. Returns an exit code."""
    from envoy.hooks import HookEvent, HookRunner

    cmd = getattr(args, "hooks_cmd", None)
    if cmd is None:
        out("Usage: envoy hooks {list,add,remove,run}")
        return 1

    raw_hooks: dict = config.get("hooks", {})  # type: ignore[attr-defined]

    if cmd == "list":
        if not raw_hooks:
            out("No hooks configured.")
            return 0
        for event, commands in raw_hooks.items():
            cmds = [commands] if isinstance(commands, str) else commands
            for c in cmds:
                out(f"  {event}: {c}")
        return 0

    if cmd == "add":
        existing = raw_hooks.get(args.event, [])
        if isinstance(existing, str):
            existing = [existing]
        if args.command not in existing:
            existing.append(args.command)
        raw_hooks[args.event] = existing
        config.set("hooks", raw_hooks)  # type: ignore[attr-defined]
        out(f"Hook added: [{args.event}] {args.command}")
        return 0

    if cmd == "remove":
        existing = raw_hooks.get(args.event, [])
        if isinstance(existing, str):
            existing = [existing]
        if args.command not in existing:
            out(f"Hook not found: [{args.event}] {args.command}")
            return 1
        existing.remove(args.command)
        raw_hooks[args.event] = existing
        config.set("hooks", raw_hooks)  # type: ignore[attr-defined]
        out(f"Hook removed: [{args.event}] {args.command}")
        return 0

    if cmd == "run":
        event = HookEvent(args.event)
        runner = HookRunner.from_config(raw_hooks)
        results = runner.run(event)
        if not results:
            out(f"No hooks registered for '{args.event}'.")
            return 0
        code = 0
        for r in results:
            status = "OK" if r.success else f"FAILED (exit {r.returncode})"
            out(f"  [{status}] {r.command}")
            if r.stderr:
                out(f"    stderr: {r.stderr}")
            if not r.success:
                code = 1
        return code

    out(f"Unknown hooks subcommand: {cmd}")
    return 1
