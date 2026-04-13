from envoy.env_version import EnvVersionManager
from envoy.parser import EnvParser


def register_version_subcommands(subparsers):
    p = subparsers.add_parser("version", help="Manage env file versions")
    sub = p.add_subparsers(dest="version_cmd")

    save_p = sub.add_parser("save", help="Save current env as a new version")
    save_p.add_argument("file", help="Path to .env file")
    save_p.add_argument("--label", default=None, help="Optional label for this version")

    list_p = sub.add_parser("list", help="List all saved versions")
    list_p.add_argument("file", help="Path to .env file")

    rollback_p = sub.add_parser("rollback", help="Rollback to a specific version")
    rollback_p.add_argument("file", help="Path to .env file")
    rollback_p.add_argument("version", type=int, help="Version number to restore")


def handle_version_command(args, manager: EnvVersionManager, out=None):
    import sys
    out = out or sys.stdout

    if not hasattr(args, "version_cmd") or args.version_cmd is None:
        out.write("Usage: envoy version {save,list,rollback}\n")
        return 1

    parser = EnvParser()

    if args.version_cmd == "save":
        try:
            with open(args.file) as f:
                vars_ = parser.parse(f.read())
        except FileNotFoundError:
            out.write(f"Error: file not found: {args.file}\n")
            return 1
        label = getattr(args, "label", None)
        entry = manager.save(vars_, label=label)
        out.write(f"Saved version {entry.version}")
        if entry.label:
            out.write(f" ({entry.label})")
        out.write(f" with {len(entry.vars)} keys\n")
        return 0

    if args.version_cmd == "list":
        result = manager.list()
        if not result.entries:
            out.write("No versions saved.\n")
            return 0
        for e in result.entries:
            label = f" [{e.label}]" if e.label else ""
            out.write(f"  v{e.version}{label} - {e.created_at} ({len(e.vars)} keys)\n")
        return 0

    if args.version_cmd == "rollback":
        vars_ = manager.rollback(args.version)
        if vars_ is None:
            out.write(f"Error: version {args.version} not found\n")
            return 1
        content = parser.serialize(vars_)
        with open(args.file, "w") as f:
            f.write(content)
        out.write(f"Rolled back to version {args.version} ({len(vars_)} keys written to {args.file})\n")
        return 0

    out.write(f"Unknown subcommand: {args.version_cmd}\n")
    return 1
