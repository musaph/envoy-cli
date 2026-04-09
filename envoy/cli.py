#!/usr/bin/env python3
"""CLI interface for envoy-cli tool."""

import argparse
import sys
import getpass
from pathlib import Path
from typing import Optional

from envoy.env_file import EnvFile
from envoy.remote import RemoteEnvManager
from envoy.storage import LocalFileStorage


class EnvoyCLI:
    """Main CLI handler for envoy commands."""

    def __init__(self):
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create and configure the argument parser."""
        parser = argparse.ArgumentParser(
            prog="envoy",
            description="Manage and sync .env files across environments using encrypted remote stores"
        )
        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # Push command
        push_parser = subparsers.add_parser("push", help="Push local .env file to remote storage")
        push_parser.add_argument("key", help="Remote key/name for the environment")
        push_parser.add_argument("--env-file", default=".env", help="Path to .env file (default: .env)")
        push_parser.add_argument("--storage-dir", default=".envoy", help="Storage directory (default: .envoy)")

        # Pull command
        pull_parser = subparsers.add_parser("pull", help="Pull .env file from remote storage")
        pull_parser.add_argument("key", help="Remote key/name for the environment")
        pull_parser.add_argument("--env-file", default=".env", help="Path to .env file (default: .env)")
        pull_parser.add_argument("--storage-dir", default=".envoy", help="Storage directory (default: .envoy)")

        # List command
        list_parser = subparsers.add_parser("list", help="List all stored environment keys")
        list_parser.add_argument("--storage-dir", default=".envoy", help="Storage directory (default: .envoy)")

        # Delete command
        delete_parser = subparsers.add_parser("delete", help="Delete a stored environment")
        delete_parser.add_argument("key", help="Remote key/name to delete")
        delete_parser.add_argument("--storage-dir", default=".envoy", help="Storage directory (default: .envoy)")

        return parser

    def run(self, args: Optional[list] = None) -> int:
        """Execute the CLI command."""
        parsed_args = self.parser.parse_args(args)

        if not parsed_args.command:
            self.parser.print_help()
            return 1

        try:
            if parsed_args.command == "push":
                return self._handle_push(parsed_args)
            elif parsed_args.command == "pull":
                return self._handle_pull(parsed_args)
            elif parsed_args.command == "list":
                return self._handle_list(parsed_args)
            elif parsed_args.command == "delete":
                return self._handle_delete(parsed_args)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

        return 0

    def _handle_push(self, args) -> int:
        """Handle push command."""
        password = getpass.getpass("Enter encryption password: ")
        storage = LocalFileStorage(args.storage_dir)
        manager = RemoteEnvManager(storage, password)
        manager.push(args.key, args.env_file)
        print(f"Successfully pushed '{args.env_file}' to '{args.key}'")
        return 0

    def _handle_pull(self, args) -> int:
        """Handle pull command."""
        password = getpass.getpass("Enter decryption password: ")
        storage = LocalFileStorage(args.storage_dir)
        manager = RemoteEnvManager(storage, password)
        manager.pull(args.key, args.env_file)
        print(f"Successfully pulled '{args.key}' to '{args.env_file}'")
        return 0

    def _handle_list(self, args) -> int:
        """Handle list command."""
        storage = LocalFileStorage(args.storage_dir)
        keys = storage.list_keys()
        if keys:
            print("Stored environments:")
            for key in sorted(keys):
                print(f"  - {key}")
        else:
            print("No stored environments found.")
        return 0

    def _handle_delete(self, args) -> int:
        """Handle delete command."""
        storage = LocalFileStorage(args.storage_dir)
        manager = RemoteEnvManager(storage, "dummy")
        manager.delete(args.key)
        print(f"Successfully deleted '{args.key}'")
        return 0


def main():
    """Entry point for the CLI."""
    cli = EnvoyCLI()
    sys.exit(cli.run())


if __name__ == "__main__":
    main()
