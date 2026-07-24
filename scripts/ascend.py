#!/usr/bin/env python3
"""deck-builder :: ascend.py — the ascension ladder (A0-A20).

Writes/updates the target repo's own ``.claude/settings.json`` (a **merge**,
never a blind overwrite — a repo may already have unrelated settings, like its
own permissions allowlist) so ``ascension_gate.py`` runs as a Stop hook,
writes ``.claude/deck-builder-ascension.json`` (the gate's config: tier +
lint/test commands), and updates ``deck.json``'s ``ascension`` field.

Deliberately does **not** parse class YAML - the ``/deck-builder:ascend``
skill reads the class file(s) and passes already-resolved ``--lint-cmd``/
``--test-cmd`` strings, the same division of labor as ``/deck-builder``
itself (scan.py detects, the skill interprets class data, the script mutates
files).

Ascension only ever moves when a human runs this - never automatically.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deck  # noqa: E402

MAX_TIER = 20
VALID_TIERS = (0, 5, 10, 15, 20)

TIER_DESCRIPTIONS = {
    0: "A0 — hooks warn only (no blocking)",
    5: "A5 — block the Stop if lint fails",
    10: "A10 — A5, plus block if tests fail",
    15: "A15 — A10, plus block on a coverage regression (best-effort)",
    20: "A20 — A15, plus every room gets a reward-curator review (not just a sample)",
}

GATE_MARKER = "ascension_gate.py"  # identifies "our" entry among other Stop hooks


def settings_path(repo: str) -> str:
    return os.path.join(repo, ".claude", "settings.json")


def ascension_config_path(repo: str) -> str:
    return os.path.join(repo, ".claude", "deck-builder-ascension.json")


def _load_json(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
            return data if isinstance(data, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_json(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")
    os.replace(tmp, path)


def _is_our_stop_entry(entry: dict) -> bool:
    for hook in entry.get("hooks", []):
        if GATE_MARKER in hook.get("command", ""):
            return True
    return False


def _merge_settings(repo: str, tier: int) -> None:
    """Add/replace/remove exactly our one Stop-hook entry; touch nothing else."""
    settings = _load_json(settings_path(repo))
    settings.setdefault("hooks", {})
    stop_list = [e for e in settings["hooks"].get("Stop", []) if not _is_our_stop_entry(e)]

    if tier >= 5:
        stop_list.append({
            "matcher": "*",
            "hooks": [{
                "type": "command",
                "command": 'python3 "${CLAUDE_PROJECT_DIR}/.claude/deck-builder/ascension_gate.py"',
                "timeout": 320,
            }],
        })

    if stop_list:
        settings["hooks"]["Stop"] = stop_list
    else:
        settings["hooks"].pop("Stop", None)
    if not settings["hooks"]:
        settings.pop("hooks", None)

    _save_json(settings_path(repo), settings)


def cmd_apply(args: argparse.Namespace) -> int:
    if args.tier not in VALID_TIERS:
        print(f"ascend.py: tier must be one of {VALID_TIERS}", file=sys.stderr)
        return 2

    _merge_settings(args.path, args.tier)
    _save_json(ascension_config_path(args.path), {
        "tier": args.tier,
        "lint_cmd": args.lint_cmd or None,
        "test_cmd": args.test_cmd or None,
        "coverage_baseline": None,
    })

    d = deck.load(args.path)
    d["ascension"] = args.tier
    deck.save(args.path, d)

    print(f"Ascended to {TIER_DESCRIPTIONS.get(args.tier, f'A{args.tier}')}")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    try:
        d = deck.load(args.path)
    except FileNotFoundError:
        print("No deck yet. Run /deck-builder first.", file=sys.stderr)
        return 1
    tier = d.get("ascension", 0)
    print(f"Current: {TIER_DESCRIPTIONS.get(tier, f'A{tier}')}")
    print()
    for t in VALID_TIERS:
        marker = "→" if t == tier else " "
        print(f" {marker} {TIER_DESCRIPTIONS[t]}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ascend.py", description="Raise or show the ascension tier."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def add_path(p: argparse.ArgumentParser) -> None:
        p.add_argument("--path", default=".", help="target repo root (default: .)")

    p_apply = sub.add_parser("apply", help="set the ascension tier")
    add_path(p_apply)
    p_apply.add_argument("--tier", type=int, required=True)
    p_apply.add_argument("--lint-cmd", default=None, help="the class's lint command, if known")
    p_apply.add_argument("--test-cmd", default=None, help="the class's test command, if known")
    p_apply.set_defaults(func=cmd_apply)

    p_show = sub.add_parser("show", help="show the current tier and the ladder")
    add_path(p_show)
    p_show.set_defaults(func=cmd_show)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
