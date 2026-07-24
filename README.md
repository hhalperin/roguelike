# deck-builder

**A roguelike deck for every repo.** A Claude Code plugin that scans any
repository, deals it a starter deck of Claude config, and grows that deck as you
clear rooms.

> Your project is the run. Your Claude config is the deck. deck-builder is the
> game engine.

| Slay the Spire | deck-builder |
|---|---|
| Card | Agent Skill (`SKILL.md`) |
| Relic | `CLAUDE.md` rule |
| Power | Hook |
| Character class | Repo archetype (detected at init) |
| Save file | `.claude/deck.json` in the target repo |

---

## What it does

Run `/deck-builder` in any repo and it will:

1. **Scan** the repo to detect its *class* (archetype) — deterministically, from
   the files present.
2. **Deal a starter deck** into the repo: `CLAUDE.md` rules (**relics**) and
   `.claude/skills/` procedures (**cards**) suited to that class.
3. **Write a save file** at `.claude/deck.json` that tracks the run.

The plugin is the game engine and holds **zero project knowledge**; everything it
knows about *your* project gets written into *your* repo, where it belongs.

## Install

```
/plugin marketplace add hhalperin/roguelike
/plugin install deck-builder@deck-builder
```

Then, in any project:

```
/deck-builder            # scan, detect class, deal the starter deck
/deck-builder:map        # show the current run state
```

<sub>Developing locally? `claude --plugin-dir ./` loads it without a marketplace,
and `claude plugin validate` checks the manifest.</sub>

## What gets dealt

```
your-repo/
├── CLAUDE.md            # relics: rules & conventions for the class
└── .claude/
    ├── deck.json        # the save file
    └── skills/          # cards: skills dealt from the class starter deck
        └── <card>/SKILL.md
```

## Classes

| Class | Detected by | Starter flavor |
|---|---|---|
| **Defect** | `pyproject.toml`, `requirements.txt` | pytest/endpoint cards, ruff & typing relics |
| **Silent** | `package.json`, `tsconfig.json` | component + test cards, strict-TS relics |
| **Ironclad** | `Dockerfile`, `*.tf`, `terraform/` | plan/drift cards, plan-before-apply relics |
| **Watcher** | `*.ipynb`, `models/`, ML deps | experiment-log + eval cards, reproducibility relics |
| **Colorless** | anything else | a minimal, safe deck |

Monorepos (strong signals across two language families) become **dual-class**
runs and share one `deck.json`.

## The save file — `deck.json`

```json
{
  "class": "defect",
  "act": 1, "floor": 0, "ascension": 0,
  "cards": [
    {"name": "add-endpoint", "type": "skill",
     "added_floor": 0, "plays": 0, "last_played": null}
  ],
  "relics": ["ruff-strict"],
  "rewards": {"offered": 0, "taken": 0, "skipped": 0}
}
```

The `taken / skipped` ratio is a deck-health metric. Good players skip most
rewards — a lean deck is a strong deck.

---

## Status & roadmap

**Act 1 — the starter deck (shipped).** `/deck-builder` init, deterministic
`scan.py`, 5 classes, `deck.json`, and `/deck-builder:map`. No hooks, no curator
— pure, useful scaffolding.

Planned:

- **Act 2 — the engine.** A `Stop`-hook reward loop, a cheap-model curator that
  offers ≤3 cards (default: **skip**), play tracking, and a campfire for
  upgrading/removing cards.
- **Act 3 — ascension.** A strictness ladder (A0–A20) that raises hook
  enforcement, plus a session-start status line.
- **The Heart — community.** Card packs, community classes, and deck export.

## Contributing

The contribution surface is markdown and YAML — new **classes** and **card
packs**, not Python. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE).
