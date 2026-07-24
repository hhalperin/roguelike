#!/usr/bin/env python3
"""record_play.py — credit a play to a dealt card.

**This file is dealt INTO target repos** at ``.claude/deck-builder/record_play.py``
by ``/deck-builder``, alongside ``deck.json``. It is deliberately self-contained
and duplicates a little logic from the engine's own ``deck.py`` rather than
importing it: a dealt card's Stop hook must keep working even if the
deck-builder plugin is later uninstalled — the save file is independent of the
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--path", default=os.environ.get("CLAUDE_PROJECT_DIR", "."))
    args = parser.parse_args()

    deck_path = os.path.join(args.path, ".claude", "deck.json")
    try:
        with open(deck_path, encoding="utf-8") as fh:
            deck = json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return 0  # never break the session over bookkeeping

    changed = False
    for card in deck.get("cards", []):
        if card.get("name") == args.name:
            card["plays"] = card.get("plays", 0) + 1
            card["last_played"] = datetime.date.today().isoformat()
            changed = True
            break

    if changed:
        tmp = deck_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(deck, fh, indent=2)
            fh.write("\n")
        os.replace(tmp, deck_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
