---
description: Show the current deck-builder run state from .claude/deck.json — class, act/floor, ascension, cards with play counts, relics, and the reward ratio.
disable-model-invocation: true
---

# /deck-builder:map — the run map

Render the current run state for this project.

1. Run:
   `python3 "${CLAUDE_SKILL_DIR}/../../scripts/deck.py" show --path "${CLAUDE_PROJECT_DIR}"`
2. Present its output as-is, then add one line of read: e.g. which cards are
   unplayed (candidates for pruning at a campfire), or whether the deck is
   approaching the ~12-card soft cap.
3. If there is no deck yet (`deck.py show` reports none), tell the user to run
   `/deck-builder` first to deal a starter deck.

Do not modify the deck here — `/deck-builder:map` is read-only.
