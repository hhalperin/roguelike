# Contributing — the modding guide

spire is built to be modded. The most valuable contributions aren't
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
commands:                # used by /spire:ascend to build gate hooks;
  lint: "..."            #   null if no command is universal enough for this
  test: "..."            #   class to enforce automatically (e.g. Colorless)
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
also register it in `classes/detection.json` (family, priority, markers,
display name). `scan.py` and `deck.py` load that file — no Python edits
required for detection or display names. The tests in `tests/test_classes.py`
enforce that the YAML, detection.json, and scripts agree. Only set `commands.lint`/`commands.test` to a
command you're confident is reasonably universal for that class — `null` (and
a warn-only gate at that tier) is the honest choice when it isn't.

### Add a card pack

A card pack is a themed set of cards (skills) that any class can draw from.
Packs land under `packs/<name>/pack.yaml` — see [`packs/README.md`](packs/README.md)
for the format. Players draw via `/spire:shop`; `scripts/pack.py list` is the
deterministic index. Open a PR adding the pack data or propose one via the
"class or card pack" issue template.

### Improve the engine

`scripts/scan.py`, `scripts/deck.py`, and `scripts/ascend.py` (plus anything
dealt into target repos: `record_play.py`, `ascension_gate.py`) are pure
standard library — **no third-party runtime dependencies**. `scripts/curator.py`
is the one documented exception (a soft dependency on `claude-agent-sdk` for
reward judgment; it must degrade to a clean "skip" if that import fails, never
raise). Follow the relics this repo deals itself (see `CLAUDE.md`): Ruff-clean,
typed, no placeholder data.

## Develop

```bash
python3 -m pytest tests/        # scan + deck + class-schema + manifest tests
python3 scripts/scan.py <repo>  # eyeball detection
ruff check scripts/ tests/      # lint (matches the repo's own relic)
```

Tests use only pytest; the class-schema and manifest tests additionally use
PyYAML and skip themselves if PyYAML isn't installed.

Optional local hooks: `pip install pre-commit && pre-commit install` runs the
same checks (`.pre-commit-config.yaml`) before each commit. CI runs them too
(`.github/workflows/ci.yml`), on a Python version matrix, alongside `pytest`
and `ruff`.

## Pull requests

- Fill in the PR template's checklist.
- CI (lint + tests, on Python 3.9 and 3.12) must pass.
- `.github/CODEOWNERS` routes review requests automatically.

## Issue labels (rarity)

- `common` — a good first issue.
- `uncommon` — a feature.
- `rare` — class design.

## License & sign-off

By contributing you agree your work is licensed under the project's
[MIT License](LICENSE). Please keep commits focused and messages clear.
