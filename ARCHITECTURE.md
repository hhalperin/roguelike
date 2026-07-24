# Architecture

How deck-builder is put together, and why.

## The one idea

**The plugin is the game engine. The target repo holds the save file.**

deck-builder (this repo) contains rules, classes, and scripts — and *zero
knowledge about any specific project*. Everything it learns about a project is
written **into that project**: `CLAUDE.md` rules, `.claude/skills/` cards, and a
`.claude/deck.json` save file. This isn't just thematic; it's forced by the
platform: a plugin's own `CLAUDE.md` is not loaded as project context, so the
engine must *write* config into repos rather than carry it.

```
 ENGINE (this repo)                        SAVE FILE (target repo)
 ┌────────────────────────┐   /deck-builder  ┌────────────────────────┐
 │ scan.py   (detect)     │  ─────────────▶  │ CLAUDE.md   (relics)   │
 │ deck.py   (save I/O)   │                  │ .claude/deck.json      │
 │ classes/  (data)       │                  │ .claude/skills/ (cards)│
 │ skills/   (commands)   │  ◀─────────────  │                        │
 └────────────────────────┘   /…:map (read)  └────────────────────────┘
```

## Deterministic before generative

The spine of the design: mechanical work is done by deterministic Python; the
model only judges where determinism can't reach.

- `scan.py` **detects** the stack (no LLM, no network, stdlib only).
- `deck.py` **validates and writes** the save file atomically (stdlib only).
- The `/deck-builder` skill **judges** which class(es) to deal and assembles the
  cards — the one place that needs a model.

A consequence: the scripts never parse the class YAML. The skill reads the class
files as prompt content, so the scripts stay dependency-free and portable.

## Components

### `scripts/scan.py` — the detector
Walks the target repo (pruning `.git`, `node_modules`, `.venv`, build/caches) and
scores five classes from marker files, directory names, dependency manifests, and
file-extension prevalence:

| Class | Family | Signals |
|---|---|---|
| defect | python | `pyproject.toml`, `setup.py`, `requirements*.txt`, `Pipfile` |
| silent | javascript | `package.json`, `tsconfig.json`, `*.ts`, framework configs |
| ironclad | infra | `Dockerfile`, `*.tf`, `terraform/`, `docker-compose*` |
| watcher | python | `*.ipynb`, `notebooks/`, `models/`, ML dependencies |
| colorless | none | (fallback when nothing scores) |

It emits JSON: `{primary, classes[], families[], monorepo, scores, signals}`.
Multiple classes within one family (e.g. a Python ML repo → `watcher` + `defect`)
are reported together but are **not** a monorepo; strong signals across two or
more *families* set `monorepo: true`, which becomes a dual-class run.

### `scripts/deck.py` — the save file
Owns `<repo>/.claude/deck.json`. Subcommands: `init`, `add-card`, `add-relic`,
`add-power`, `show`, `validate`. Writes are atomic (temp file + `os.replace`) and
`init` is idempotent (refuses to re-deal without `--force`). `show` backs
`/deck-builder:map`.

### `classes/*.yaml` — the archetypes (data)
Each class file declares its `detected_by` signals, `flavor`, `relics`
(CLAUDE.md rules), and `cards` (each a `name` + `description` + SKILL.md `body`).
This is the primary contribution surface — adding an archetype is a data change,
not a code change.

### `skills/` — the commands and rubrics
- `deck-builder/` → `/deck-builder` (Neow's blessing: scan → deal), user-invoked.
- `map/` → `/deck-builder:map` (render run state), user-invoked.
- `card-evaluation/`, `deck-state/` → model-invoked rubrics that guide Claude when
  judging what belongs in a deck and how to touch `deck.json` safely.

Skills reference bundled scripts via `${CLAUDE_SKILL_DIR}/../../scripts/…` and the
target repo via `${CLAUDE_PROJECT_DIR}`, so paths stay install-independent.

## `deck.json` schema (v1)

```json
{
  "schema_version": 1,
  "class": "defect",
  "classes": ["defect"],
  "act": 1, "floor": 0, "ascension": 0,
  "created": "YYYY-MM-DD",
  "cards": [{"name": "…", "type": "skill", "added_floor": 0, "plays": 0, "last_played": null}],
  "relics": ["…"],
  "powers": [{"event": "…", "name": "…"}],
  "rooms_cleared": [],
  "clean_room_streak": 0,
  "rewards": {"offered": 0, "taken": 0, "skipped": 0}
}
```

`rewards.taken / rewards.skipped` is a deck-health signal — a high skip rate is
healthy. `ascension` (0–20) is raised only by the (planned) `ascend` command,
never silently; `clean_room_streak` is reserved for a future opt-in auto-raise.

## Extending

- **Add a class:** create `classes/<name>.yaml`, register the name in
  `scripts/scan.py` (`FAMILY` + detection) and `scripts/deck.py` (`CLASS_NAMES`).
  `tests/test_classes.py` enforces that the data and code agree.
- **Add a card pack:** see `packs/README.md`.

## Status

Act 1 (the starter deck) is what ships today. Act 2 (a `Stop`-hook reward loop
and a cheap-model curator), Act 3 (the ascension ladder), and community card
packs are planned — see the roadmap in [README.md](README.md).
