---
description: How to read and write a deck-builder save file (.claude/deck.json) safely — its schema, invariants, and the rule to always go through deck.py rather than hand-editing the JSON.
when_to_use: When reading, updating, or reasoning about a repo's .claude/deck.json deck-builder save file.
user-invocable: false
---

# Deck state (deck.json) — read/write safely

The save file lives **with the target project** at `<repo>/.claude/deck.json`,
not with the plugin. Treat it as the single source of truth for a run.

## Golden rule

**Never hand-edit `deck.json`.** Go through the engine script so writes stay
atomic and the schema stays valid:

- Read / render: `deck.py show --path <repo>`
- Validate: `deck.py validate --path <repo>`
- Create: `deck.py init --path <repo> --class <class>`
- Record a card / relic / power: `deck.py add-card | add-relic | add-power`

`deck.py` lives at `${CLAUDE_SKILL_DIR}/../../scripts/deck.py`. It writes to a
temp file and `os.replace`s it, so a crash never leaves a half-written deck.

## Schema (v1)

```json
{
  "schema_version": 1,
  "class": "defect",
  "classes": ["defect"],
  "act": 1,
  "floor": 0,
  "ascension": 0,
  "created": "YYYY-MM-DD",
  "cards": [
    {"name": "add-endpoint", "type": "skill",
     "added_floor": 0, "plays": 0, "last_played": null}
  ],
  "relics": ["ruff-strict"],
  "powers": [{"event": "PostToolUse", "name": "auto-format"}],
  "rooms_cleared": [],
  "clean_room_streak": 0,
  "rewards": {"offered": 0, "taken": 0, "skipped": 0}
}
```

## Invariants

- `class` is the primary; `classes` lists all classes (dual-class monorepos).
- `cards[].type` is one of `skill`, `relic`, `power`.
- `rewards.taken / rewards.skipped` is a deck-health signal — a high skip rate is
  good. Don't optimize for "taken".
- `ascension` (0–20) is raised only by `/deck-builder:ascend` (manual), never
  silently. `clean_room_streak` is reserved for a future opt-in auto-raise.
- If `deck.py validate` fails, fix the deck before writing anything else.
