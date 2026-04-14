"""CLI subcommands for env archive management."""
from __future__ import annotations

import json
from typing import Any

from envoy.env_archive import EnvArchiveManager


def register_archive_subcommands(subparsers: Any) -> None:
    p = subparsers.add_parser("archive", help="Archive and restore env variable sets")
    sub = p.add_subparsers(dest="archive_cmd")

    save_p = sub.add_parser("save", help="Save current vars under a label")
    save_p.add_argument("--file", required=True, help="Path to .env file")
    save_p.add_argument("--label", required=True, help="Archive label")
    save_p.add_argument("--store", default=".envoy_archives.json", help="Archive store path")

    restore_p = sub.add_parser("restore", help="Restore vars from a label")
    restore_p.add_argument("--label", required=True, help="Archive label to restore")
    restore_p.add_argument("--store", default=".envoy_archives.json", help="Archive store path")

    list_p = sub.add_parser("list", help="List all archived labels")
    list_p.add_argument("--store", default=".envoy_archives.json", help="Archive store path")

    delete_p = sub.add_parser("delete", help="Delete an archived label")
    delete_p.add_argument("--label", required=True, help="Archive label to delete")
    delete_p.add_argument("--store", default=".envoy_archives.json", help="Archive store path")


def _load_manager(store_path: str) -> EnvArchiveManager:
    import os
    mgr = EnvArchiveManager()
    if os.path.exists(store_path):
        with open(store_path) as f:
            mgr.load_from_dict_list(json.load(f))
    return mgr


def _save_manager(mgr: EnvArchiveManager, store_path: str) -> None:
    with open(store_path, "w") as f:
        json.dump(mgr.to_dict_list(), f, indent=2)


def handle_archive_command(args: Any, out=print) -> int:
    if not hasattr(args, "archive_cmd") or args.archive_cmd is None:
        out("Usage: envoy archive <save|restore|list|delete>")
        return 1

    if args.archive_cmd == "save":
        from envoy.parser import EnvParser
        with open(args.file) as f:
            vars_ = EnvParser.parse(f.read())
        mgr = _load_manager(args.store)
        entry = mgr.save(args.label, vars_)
        _save_manager(mgr, args.store)
        out(f"Archived {len(vars_)} vars under label '{args.label}' (checksum: {entry.checksum[:8]}…)")
        return 0

    if args.archive_cmd == "restore":
        mgr = _load_manager(args.store)
        vars_ = mgr.restore(args.label)
        if vars_ is None:
            out(f"Error: label '{args.label}' not found in archive.")
            return 1
        for k, v in vars_.items():
            out(f"{k}={v}")
        return 0

    if args.archive_cmd == "list":
        mgr = _load_manager(args.store)
        entries = mgr.list_entries()
        if not entries:
            out("No archives found.")
        for e in entries:
            out(f"  {e.label}  ({e.created_at})  keys={len(e.vars)}")
        return 0

    if args.archive_cmd == "delete":
        mgr = _load_manager(args.store)
        removed = mgr.delete(args.label)
        if not removed:
            out(f"Error: label '{args.label}' not found.")
            return 1
        _save_manager(mgr, args.store)
        out(f"Deleted archive '{args.label}'.")
        return 0

    out(f"Unknown archive subcommand: {args.archive_cmd}")
    return 1
