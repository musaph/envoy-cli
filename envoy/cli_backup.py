"""CLI subcommands for backup/restore of .env files."""
from __future__ import annotations

import argparse
from typing import Any

from envoy.backup import EnvBackupManager
from envoy.parser import EnvParser


def register_backup_subcommands(subparsers: Any) -> None:
    p = subparsers.add_parser("backup", help="Backup and restore .env files")
    sub = p.add_subparsers(dest="backup_cmd")

    cr = sub.add_parser("create", help="Create a backup of a .env file")
    cr.add_argument("file", help="Path to .env file")
    cr.add_argument("--key", default="default", help="Backup key/label")
    cr.add_argument("--note", default="", help="Optional note")

    ls = sub.add_parser("list", help="List backups")
    ls.add_argument("--key", default=None, help="Filter by key")

    rs = sub.add_parser("restore", help="Restore a backup")
    rs.add_argument("key", help="Backup key to restore")
    rs.add_argument("--index", type=int, default=-1, help="Which backup to restore (default: latest)")
    rs.add_argument("--out", default=None, help="Output file path")

    dl = sub.add_parser("delete", help="Delete all backups for a key")
    dl.add_argument("key", help="Backup key to delete")


def handle_backup_command(args: Any, backup_dir: str, output=None) -> int:
    import sys
    out = output or sys.stdout
    mgr = EnvBackupManager(backup_dir)
    cmd = getattr(args, "backup_cmd", None)

    if cmd is None:
        out.write("Usage: envoy backup {create,list,restore,delete}\n")
        return 1

    if cmd == "create":
        try:
            with open(args.file, "r", encoding="utf-8") as fh:
                content = fh.read()
        except FileNotFoundError:
            out.write(f"Error: file not found: {args.file}\n")
            return 1
        vars_ = EnvParser.parse(content)
        entry = mgr.create(key=args.key, vars=vars_, note=args.note)
        out.write(f"Backup created: {entry}\n")
        return 0

    if cmd == "list":
        entries = mgr.list_backups(key=args.key)
        if not entries:
            out.write("No backups found.\n")
        for e in entries:
            out.write(f"  [{e.key}] {e.timestamp}  vars={len(e.vars)}  note={e.note!r}\n")
        return 0

    if cmd == "restore":
        entry = mgr.restore(args.key, index=args.index)
        if entry is None:
            out.write(f"No backup found for key: {args.key}\n")
            return 1
        content = EnvParser.serialize(entry.vars)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as fh:
                fh.write(content)
            out.write(f"Restored {len(entry.vars)} vars to {args.out}\n")
        else:
            out.write(content)
        return 0

    if cmd == "delete":
        removed = mgr.delete(args.key)
        out.write(f"Deleted {removed} backup(s) for key: {args.key}\n")
        return 0

    out.write(f"Unknown backup subcommand: {cmd}\n")
    return 1
