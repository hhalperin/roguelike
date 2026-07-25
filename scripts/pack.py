#!/usr/bin/env python3
"""spire :: pack.py — list and locate community card packs.

Packs are authored as ``packs/<name>/pack.yaml`` (same card/relic shape as
classes). This script stays stdlib-only and does **not** parse the YAML —
listing and path resolution are deterministic; ``/spire:shop`` (and campfire)
read the pack file as prompt content the same way ``/spire`` reads class YAML.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

PACKS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "packs")


def _is_safe_pack_name(name: str) -> bool:
    if not name or name in (os.curdir, os.pardir):
        return False
    if os.sep in name or (os.altsep and os.altsep in name):
        return False
    return True


def list_packs(packs_dir: str = PACKS_DIR) -> list[dict]:
    """Return ``[{name, path}]`` for every directory that has a pack.yaml."""
    root = os.path.abspath(packs_dir)
    if not os.path.isdir(root):
        return []
    found: list[dict] = []
    for entry in sorted(os.listdir(root)):
        if not _is_safe_pack_name(entry):
            continue
        pack_yaml = os.path.join(root, entry, "pack.yaml")
        if os.path.isfile(pack_yaml):
            found.append({"name": entry, "path": pack_yaml})
    return found


def pack_path(name: str, packs_dir: str = PACKS_DIR) -> str | None:
    if not _is_safe_pack_name(name):
        return None
    path = os.path.join(os.path.abspath(packs_dir), name, "pack.yaml")
    return path if os.path.isfile(path) else None


def cmd_list(args: argparse.Namespace) -> int:
    packs = list_packs(args.packs_dir)
    if args.json:
        print(json.dumps(packs, indent=2))
        return 0
    if not packs:
        print("No packs found.")
        return 0
    for p in packs:
        print(f"{p['name']:<24} {p['path']}")
    return 0


def cmd_path(args: argparse.Namespace) -> int:
    path = pack_path(args.name, args.packs_dir)
    if not path:
        print(f"pack.py: unknown pack {args.name!r}", file=sys.stderr)
        return 1
    print(path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pack.py", description="List and locate spire card packs."
    )
    parser.add_argument(
        "--packs-dir",
        default=PACKS_DIR,
        help="packs root (default: plugin packs/)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="list available packs")
    p_list.add_argument("--json", action="store_true", help="emit JSON")
    p_list.set_defaults(func=cmd_list)

    p_path = sub.add_parser("path", help="print the pack.yaml path for a pack")
    p_path.add_argument("name", help="pack directory name")
    p_path.set_defaults(func=cmd_path)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
