#!/usr/bin/env python3
"""deck-builder :: activity_log.py — PostToolUse hook: count activity.

Fires after every tool call. Deliberately does almost nothing: if the current
directory hasn't been dealt a deck, it's a silent no-op. Otherwise it bumps a
counter that the Stop hook (``reward_gate.py``) reads to decide whether
enough happened this session to be worth judging for a reward. No git calls,
no LLM calls, no network — this hook must stay fast and always succeed.

Reads ``CLAUDE_PROJECT_DIR`` from the environment (the project root Claude
Code hooks always receive); falls back to the current directory so the
script is still testable/runnable standalone.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine_state  # noqa: E402

CAP = 999  # avoid unbounded growth; anything past this is "plenty of activity"


def main() -> int:
    repo = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    try:
        if not engine_state.deck_exists(repo):
            return 0
        state = engine_state.load(repo)
        state["activity_count"] = min(CAP, int(state.get("activity_count", 0)) + 1)
        engine_state.save(repo, state)
    except Exception:
        # Never let bookkeeping break the user's session.
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
