#!/usr/bin/env python3
"""spire :: status_line.py — SessionStart hook: show the run.

Prints a one-or-two-line status to stdout, which Claude Code adds directly to
the new session's context (no JSON wrapping needed for SessionStart). Silent
(no output at all) when the current project has no deck.json - most repos a
user opens will never have run ``/spire``, and this hook must not add
noise to sessions that have nothing to do with a deck.

This is also where a reward the Stop hook detected last session gets
surfaced - non-intrusively, at the next natural checkpoint - per the design's
"detect at Stop, present at SessionStart" reward UX.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deck  # noqa: E402
import engine_state  # noqa: E402

CLASS_LABELS = deck.CLASS_NAMES


def render(repo: str) -> str | None:
    if not engine_state.deck_exists(repo):
        return None
    try:
        d = deck.load(repo)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

    names = d.get("classes") or [d.get("class", "colorless")]
    label = " + ".join(CLASS_LABELS.get(c, c) for c in names)
    lines = [
        f"🎴 spire: {label} · Act {d.get('act', 1)} · Floor {d.get('floor', 0)}"
        f" · Ascension {d.get('ascension', 0)} — {len(d.get('cards', []))} cards,"
        f" {len(d.get('relics', []))} relics."
    ]

    pending = engine_state.load_pending_reward(repo)
    if pending is not None:
        offer_names = ", ".join(o.get("name", "?") for o in pending["offer"])
        lines.append(
            f"🎁 Card(s) pending review: {offer_names} — run /spire:campfire to decide."
        )

    return "\n".join(lines)


def main() -> int:
    repo = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    try:
        text = render(repo)
    except Exception:
        text = None
    if text:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
