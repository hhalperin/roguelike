# Contributing — the modding guide

deck-builder is built to be modded. The most valuable contributions aren't
Python — they're **classes** and **card packs**, written in markdown and YAML.
Low barrier, high creativity. This is the Slay-the-Spire modding scene, on
purpose.

## Ways to contribute

### Add or improve a class (an archetype)

A class is one file: `classes/<name>.yaml`. Copy an existing one and adjust.
Schema:

```yaml
class: <name>            # must equal the filename stem
name: The <Name>         # display name
detected_by: [ ... ]     # human-readable list of the signals that pick this class
flavor: >-               # one or two sentences of theme
  ...
relics:                  # rules written into the target repo's CLAUDE.md
  - id: <kebab-id>
    rule: "A durable rule or boundary."
cards:                   # skills dealt into the target repo's .claude/skills/
  - name: <kebab-name>
    description: "Frontmatter description — when Claude should use this skill."
    body: |
      # <Card title>
      Step-by-step instructions for the skill body.
powers: []               # hooks (empty for now)
agent: null              # optional standing subagent
```

Keep starter decks **small and sharp** — a couple of relics and cards. Players
earn more by clearing rooms; don't front-load. If you add a brand-new class name,
also register it in `scripts/scan.py` (`FAMILY`, and detection signals) and
`scripts/deck.py` (`CLASS_NAMES`); the tests in `tests/test_classes.py` enforce
that the data and code agree.

### Add a card pack

A card pack is a themed set of cards (skills) that any class can draw from.
Packs land under `packs/` (coming with Act 2). For now, propose them as an issue.

### Improve the engine

`scripts/scan.py` (detection) and `scripts/deck.py` (the save file) are pure
standard library — **no third-party runtime dependencies**. Follow the relics
this repo deals itself (see `CLAUDE.md`): Ruff-clean, typed, no placeholder data.

## Develop

```bash
python3 -m pytest tests/        # scan + deck + class-schema tests
python3 scripts/scan.py <repo>  # eyeball detection
ruff check .                    # lint (optional, matches the repo's relic)
```

Tests use only pytest; the class-schema test additionally uses PyYAML and skips
itself if PyYAML isn't installed.

## Issue labels (rarity)

- `common` — a good first issue.
- `uncommon` — a feature.
- `rare` — class design.

## License & sign-off

By contributing you agree your work is licensed under the project's
[MIT License](LICENSE). Please keep commits focused and messages clear.
