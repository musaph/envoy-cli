"""CLI subcommands for compress/decompress operations on env files."""

import argparse
from pathlib import Path

from envoy.compress import EnvCompressor
from envoy.parser import EnvParser


def register_compress_subcommands(subparsers: argparse._SubParsersAction) -> None:
    compress_parser = subparsers.add_parser(
        "compress", help="Compress and decompress .env files"
    )
    compress_sub = compress_parser.add_subparsers(
        dest="compress_cmd", metavar="{pack,unpack,stats}"
    )

    pack = compress_sub.add_parser("pack", help="Compress an env file to binary")
    pack.add_argument("file", help="Path to .env file")
    pack.add_argument("-o", "--output", help="Output file path", default=None)
    pack.add_argument("-l", "--level", type=int, default=6, help="Compression level 0-9")

    unpack = compress_sub.add_parser("unpack", help="Decompress a packed env file")
    unpack.add_argument("file", help="Path to compressed file")
    unpack.add_argument("-o", "--output", help="Output .env file path", default=None)

    stats_p = compress_sub.add_parser("stats", help="Show compression stats for a file")
    stats_p.add_argument("file", help="Path to .env file")


def handle_compress_command(args: argparse.Namespace, out=print) -> int:
    cmd = getattr(args, "compress_cmd", None)
    if not cmd:
        out("Usage: envoy compress {pack,unpack,stats}")
        return 1

    compressor = EnvCompressor(level=getattr(args, "level", 6))

    if cmd == "pack":
        src = Path(args.file)
        if not src.exists():
            out(f"Error: file not found: {src}")
            return 1
        raw = src.read_bytes()
        compressed = compressor.compress(raw)
        dest = Path(args.output) if args.output else src.with_suffix(".env.zz")
        dest.write_bytes(compressed)
        stats = compressor.stats(raw, compressed)
        out(f"Packed {src} -> {dest} ({stats})")
        return 0

    if cmd == "unpack":
        src = Path(args.file)
        if not src.exists():
            out(f"Error: file not found: {src}")
            return 1
        compressed = src.read_bytes()
        try:
            raw = compressor.decompress(compressed)
        except Exception as exc:
            out(f"Error: failed to decompress: {exc}")
            return 1
        dest = Path(args.output) if args.output else src.with_suffix(".env")
        dest.write_bytes(raw)
        out(f"Unpacked {src} -> {dest}")
        return 0

    if cmd == "stats":
        src = Path(args.file)
        if not src.exists():
            out(f"Error: file not found: {src}")
            return 1
        raw = src.read_bytes()
        compressed = compressor.compress(raw)
        stats = compressor.stats(raw, compressed)
        out(str(stats))
        return 0

    out(f"Unknown compress subcommand: {cmd}")
    return 1
