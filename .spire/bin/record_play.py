#!/usr/bin/env python3
"""record_play.py — credit a play to a dealt card.

**This file is dealt INTO target repos** at ``.spire/bin/record_play.py``
by ``/spire``, alongside ``.spire/deck.json``. It is deliberately self-contained
and duplicates a little logic from the engine's own ``deck.py`` rather than
importing it: a dealt card's Stop hook must keep working even if the
spire plugin is later uninstalled — the save file is independent of the
engine that dealt it. Pure stdlib, no engine imports.

Each dealt card's own SKILL.md frontmatter defines a Stop hook (scoped to that
skill's lifecycle - it only fires while the skill is active) that calls this
script with ``--name <card-name>``, so a play is credited once per session in
which the card was used.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys


def _read_session_id() -> str | None:
    """Best-effort read of the Stop hook's stdin JSON for ``session_id``.

    Claude Code pipes the hook payload to the process's stdin and closes it;
    a manual/test invocation with nothing piped in reads as an immediate
    EOF, which falls back to "unknown session" (always credit the play)
    rather than risk ever blocking on a read.
    """
    try:
        raw = sys.stdin.read()
    except Exception:
        return None
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return data.get("session_id") if isinstance(data, dict) else None


def _resolve_deck_path(repo: str) -> str:
    """Prefer ``.spire/deck.json``; fall back to a legacy ``.claude/deck.json``."""
    spire = os.path.join(repo, ".spire", "deck.json")
    if os.path.exists(spire):
        return spire
    legacy = os.path.join(repo, ".claude", "deck.json")
    if os.path.exists(legacy):
        return legacy
    return spire


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--path", default=os.environ.get("CLAUDE_PROJECT_DIR", "."))
    args = parser.parse_args()

    session_id = _read_session_id()

    deck_file = _resolve_deck_path(args.path)
    try:
        with open(deck_file, encoding="utf-8") as fh:
            deck = json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return 0  # never break the session over bookkeeping

    changed = False
    for card in deck.get("cards", []):
        if card.get("name") != args.name:
            continue
        if session_id and card.get("last_play_session") == session_id:
            break  # already credited this session - no-op, per-session guard
        card["plays"] = card.get("plays", 0) + 1
        card["last_played"] = datetime.date.today().isoformat()
        if session_id:
            card["last_play_session"] = session_id
        changed = True
        break

    if changed:
        tmp = deck_file + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(deck, fh, indent=2)
            fh.write("\n")
        os.replace(tmp, deck_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
