# CLAUDE.md — deck-builder engine

This repo is the **game engine** for the `deck-builder` Claude Code plugin. It
contains rules, classes, scripts, and skills — and **zero project knowledge**
about any target repo. The knowledge deck-builder produces is *written into other
repos*, never carried here.

## Mental model

| deck-builder term | Reality |
| :-- | :-- |
| Deal a deck | Write `CLAUDE.md` + `.claude/skills/` + `.claude/deck.json` into a target repo |
| Card | A skill (`SKILL.md`) |
| Relic | A `CLAUDE.md` rule |
| Power | A hook |
| Class | A repo archetype detected by `scan.py` |
| Save file | `.claude/deck.json` in the target repo |

**Engine vs save file:** this repo is the engine. The save file lives with the
project being decked. Keep that separation — nothing here should hard-code facts
about a specific target project.

## Conventions

- **Scripts are pure standard library.** `scripts/scan.py` and `scripts/deck.py`
  must import only the stdlib (no third-party runtime deps) so they run in any
  repo's environment. `json` and `argparse` only.
- **Scripts don't parse class YAML.** The `/deck-builder` skill reads the class
  files itself; the scripts stay data-format-agnostic. PyYAML is a *test-only*
  convenience (see `tests/test_classes.py`, which skips if it's absent).
- **Classes are data, not code.** Add archetypes as `classes/<name>.yaml`. The
  contribution surface is markdown and YAML — that's deliberate.
- **Deterministic before generative.** `scan.py` detects, `deck.py` validates;
  the model only judges (which class, which cards) where determinism can't.
- **Skills reference bundled files via `${CLAUDE_SKILL_DIR}`** and target the repo
  via `${CLAUDE_PROJECT_DIR}` — never absolute or install-specific paths.

## Layout

```
.claude-plugin/   plugin.json + marketplace.json (ONLY these live here)
skills/           plugin skills: deck-builder, map, card-evaluation, deck-state
scripts/          scan.py (detect), deck.py (save-file I/O) — stdlib only
classes/          the 5 archetypes as YAML data
tests/            pytest over the scripts + class schema
```

## Develop

- Run tests: `python3 -m pytest tests/`
- Try the detector: `python3 scripts/scan.py <some-repo>`
- Validate the plugin (needs the Claude Code CLI): `claude plugin validate`,
  then `claude --plugin-dir ./` and `/help` should list `/deck-builder`.

## deck-builder relics

<!-- Dogfood: this repo runs its own deck (class: defect). These relics were
     dealt by /deck-builder and apply to the engine's own Python code. -->

- Lint and format with Ruff; resolve every warning before committing.
- Type-hint public functions and keep the type checker (mypy/pyright) clean.
- Never ship mock, stub, or placeholder data in production code paths.
