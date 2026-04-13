"""CLI subcommands for env namespace management."""
from typing import Any
from envoy.env_namespace import EnvNamespaceManager
from envoy.parser import EnvParser


def register_namespace_subcommands(subparsers: Any) -> None:
    ns_parser = subparsers.add_parser("namespace", help="Manage env var namespaces")
    ns_sub = ns_parser.add_subparsers(dest="ns_cmd")

    # list
    p_list = ns_sub.add_parser("list", help="List all namespaces in a .env file")
    p_list.add_argument("file", help="Path to .env file")

    # extract
    p_extract = ns_sub.add_parser("extract", help="Extract vars for a namespace")
    p_extract.add_argument("file", help="Path to .env file")
    p_extract.add_argument("namespace", help="Namespace prefix (e.g. DB)")
    p_extract.add_argument("--strip", action="store_true",
                           help="Strip the namespace prefix from output keys")

    # remove
    p_remove = ns_sub.add_parser("remove", help="Remove all vars in a namespace")
    p_remove.add_argument("file", help="Path to .env file")
    p_remove.add_argument("namespace", help="Namespace prefix to remove")


def _read_env_file(path: str, out) -> tuple:
    """Read and parse a .env file, returning (vars_dict, error_code).

    Returns (parsed_vars, 0) on success, or (None, error_code) on failure.
    """
    try:
        with open(path, "r") as fh:
            content = fh.read()
    except FileNotFoundError:
        out(f"Error: file not found: {path}")
        return None, 2
    except OSError as exc:
        out(f"Error: could not read file '{path}': {exc}")
        return None, 2

    parser = EnvParser()
    return parser.parse(content), 0


def handle_namespace_command(args: Any, out=print) -> int:
    if not hasattr(args, "ns_cmd") or args.ns_cmd is None:
        out("Usage: envoy namespace <list|extract|remove> [options]")
        return 1

    vars_, err = _read_env_file(args.file, out)
    if err:
        return err

    manager = EnvNamespaceManager()

    if args.ns_cmd == "list":
        namespaces = manager.list_namespaces(vars_)
        if not namespaces:
            out("No namespaces found.")
        else:
            for ns in namespaces:
                out(ns)
        return 0

    if args.ns_cmd == "extract":
        result = manager.extract(vars_, args.namespace)
        source = result.stripped if args.strip else result.vars
        if not source:
            out(f"No vars found for namespace '{args.namespace}'.")
        else:
            for key, value in source.items():
                out(f"{key}={value}")
        return 0

    if args.ns_cmd == "remove":
        updated = manager.remove_namespace(vars_, args.namespace)
        removed = len(vars_) - len(updated)
        out(f"Removed {removed} var(s) under namespace '{args.namespace}'.")
        return 0

    out(f"Unknown namespace subcommand: {args.ns_cmd}")
    return 1
