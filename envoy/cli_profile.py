"""CLI sub-commands for profile management in envoy-cli."""

from __future__ import annotations

from typing import List

from envoy.profile import Profile, ProfileManager


def register_profile_subcommands(subparsers) -> None:
    """Attach 'profile' sub-command group to an existing argparse subparsers action."""
    profile_parser = subparsers.add_parser("profile", help="Manage environment profiles")
    profile_sub = profile_parser.add_subparsers(dest="profile_command", metavar="<command>")

    # profile create
    create_p = profile_sub.add_parser("create", help="Create a new profile")
    create_p.add_argument("name", help="Profile name")
    create_p.add_argument("-d", "--description", default="", help="Optional description")
    create_p.add_argument("-t", "--tag", dest="tags", action="append", default=[], metavar="TAG")

    # profile list
    profile_sub.add_parser("list", help="List all profiles")

    # profile show
    show_p = profile_sub.add_parser("show", help="Show profile details")
    show_p.add_argument("name", help="Profile name")

    # profile delete
    del_p = profile_sub.add_parser("delete", help="Delete a profile")
    del_p.add_argument("name", help="Profile name")


def handle_profile_command(args, config, out) -> int:
    """Dispatch profile sub-commands. Returns exit code."""
    manager = ProfileManager(config)
    cmd = getattr(args, "profile_command", None)

    if cmd is None:
        out.write("Usage: envoy profile <create|list|show|delete>\n")
        return 1

    if cmd == "create":
        try:
            profile = Profile(name=args.name, description=args.description, tags=args.tags)
            manager.create(profile)
            out.write(f"Profile '{args.name}' created.\n")
            return 0
        except (ValueError, KeyError) as exc:
            out.write(f"Error: {exc}\n")
            return 1

    if cmd == "list":
        profiles = manager.list_profiles()
        if not profiles:
            out.write("No profiles defined.\n")
        else:
            for p in profiles:
                desc = f"  # {p.description}" if p.description else ""
                out.write(f"  {p.name}{desc}\n")
        return 0

    if cmd == "show":
        p = manager.get(args.name)
        if p is None:
            out.write(f"Error: Profile '{args.name}' not found.\n")
            return 1
        out.write(f"Name:        {p.name}\n")
        out.write(f"Description: {p.description}\n")
        out.write(f"Tags:        {', '.join(p.tags) or '-'}\n")
        if p.metadata:
            for k, v in p.metadata.items():
                out.write(f"  {k}: {v}\n")
        return 0

    if cmd == "delete":
        if manager.delete(args.name):
            out.write(f"Profile '{args.name}' deleted.\n")
            return 0
        out.write(f"Error: Profile '{args.name}' not found.\n")
        return 1

    out.write(f"Unknown profile command: {cmd}\n")
    return 1
