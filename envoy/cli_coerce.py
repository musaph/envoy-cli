"""CLI subcommands for env var value coercion."""
from envoy.env_coerce import EnvCoercer
from envoy.parser import EnvParser


def register_coerce_subcommands(subparsers) -> None:
    p = subparsers.add_parser("coerce", help="Coerce env var values using named rules")
    sub = p.add_subparsers(dest="coerce_cmd")

    run_p = sub.add_parser("run", help="Apply coercion rules to a .env file")
    run_p.add_argument("file", help="Path to .env file")
    run_p.add_argument(
        "--rules",
        nargs="+",
        default=["strip"],
        metavar="RULE",
        help="Coercion rules to apply (strip, lowercase, uppercase, bool_normalize, strip_quotes)",
    )
    run_p.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without writing",
    )

    sub.add_parser("rules", help="List available coercion rules")


def handle_coerce_command(args, out=None) -> int:
    import sys
    out = out or sys.stdout

    if not hasattr(args, "coerce_cmd") or args.coerce_cmd is None:
        out.write("Usage: envoy coerce <run|rules>\n")
        return 1

    if args.coerce_cmd == "rules":
        out.write("Available coercion rules:\n")
        for name in EnvCoercer.RULES:
            out.write(f"  {name}\n")
        return 0

    if args.coerce_cmd == "run":
        import os
        if not os.path.exists(args.file):
            out.write(f"Error: file not found: {args.file}\n")
            return 1
        try:
            coercer = EnvCoercer(rules=args.rules)
        except ValueError as exc:
            out.write(f"Error: {exc}\n")
            return 1

        with open(args.file) as fh:
            content = fh.read()

        parser = EnvParser()
        vars_ = parser.parse(content)
        result = coercer.coerce(vars_)

        if not result.has_changes:
            out.write("No changes needed.\n")
            return 0

        for change in result.changes:
            out.write(f"  {change.key}: {change.original!r} -> {change.coerced!r} [{change.rule}]\n")

        if not args.dry_run:
            coerced_vars = {**vars_}
            for change in result.changes:
                coerced_vars[change.key] = change.coerced
            new_content = parser.serialize(coerced_vars)
            with open(args.file, "w") as fh:
                fh.write(new_content)
            out.write(f"Written {len(result.changes)} change(s) to {args.file}\n")
        else:
            out.write(f"Dry run: {len(result.changes)} change(s) not written.\n")

        return 0

    out.write(f"Unknown coerce subcommand: {args.coerce_cmd}\n")
    return 1
