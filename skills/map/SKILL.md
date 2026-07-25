---
description: Show the current deck-builder run state from .claude/deck.json — class, act/floor, ascension, cards with play counts, relics, and the reward ratio.
disable-model-invocation: true
allowed-tools: Bash(python3 "${CLAUDE_SKILL_DIR}/../../scripts/deck.py" *)
---

# /deck-builder:map — the run map

Render the current run state for this project.

1. Run:
   `python3 "${CLAUDE_SKILL_DIR}/../../scripts/deck.py" show --path "${CLAUDE_PROJECT_DIR}"`
2. Then run:
   `python3 "${CLAUDE_SKILL_DIR}/../../scripts/deck.py" stats --path "${CLAUDE_PROJECT_DIR}"`
   for the deterministic health read — unplayed cards, the most-played card,
   soft-cap status, and the reward take rate — rather than eyeballing it from
   `show`'s raw list.
3. Present both outputs together as one coherent run summary.
4. If there is no deck yet (either command reports none), tell the user to run
   `/deck-builder` first to deal a starter deck.

Do not modify the deck here — `/deck-builder:map` is read-only.
