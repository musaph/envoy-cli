import argparse
from typing import Optional

from envoy.env_shuffle import EnvShuffler
from envoy.parser import EnvParser


def register_shuffle_subcommands(subparsers) -> None:
    p = subparsers.add_parser("shuffle", help="Randomly reorder variables in a .env file")
    sub = p.add_subparsers(dest="shuffle_cmd")

    run_p = sub.add_parser("run", help="Shuffle and print result")
    run_p.add_argument("file", help="Path to .env file")
    run_p.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    run_p.add_argument("--in-place", action="store_true", help="Write shuffled output back to file")


def handle_shuffle_command(args, out=None) -> int:
    import sys
    out = out or sys.stdout

    if not hasattr(args, "shuffle_cmd") or args.shuffle_cmd is None:
        out.write("Usage: envoy shuffle <subcommand>\n")
        out.write("Subcommands: run\n")
        return 1

    if args.shuffle_cmd == "run":
        return _run_shuffle(args, out)

    out.write(f"Unknown subcommand: {args.shuffle_cmd}\n")
    return 1


def _run_shuffle(args, out) -> int:
    import os

    if not os.path.isfile(args.file):
        out.write(f"Error: file not found: {args.file}\n")
        return 1

    with open(args.file, "r") as fh:
        content = fh.read()

    parser = EnvParser()
    vars_ = parser.parse(content)

    seed: Optional[int] = getattr(args, "seed", None)
    shuffler = EnvShuffler(seed=seed)
    result = shuffler.shuffle(vars_)

    serialized = parser.serialize(result.vars)

    if getattr(args, "in_place", False):
        with open(args.file, "w") as fh:
            fh.write(serialized)
        out.write(f"Shuffled {len(result.shuffled_order)} variables in {args.file}\n")
    else:
        out.write(serialized)

    return 0
