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
| Ascension | A0–A20 strictness ladder for the same hooks |

---

## What it does

Run `/deck-builder` in any repo and it will:

1. **Scan** the repo to detect its *class* (archetype) — deterministically, from
   the files present.
2. **Deal a starter deck** into the repo: `CLAUDE.md` rules (**relics**) and
   `.claude/skills/` procedures (**cards**) suited to that class.
3. **Write a save file** at `.claude/deck.json` that tracks the run.

From there, the deck **grows on its own**: a `Stop` hook watches for real work
(a new commit, meaningful activity) and — only when a pattern has genuinely
repeated — a cheap-model curator offers up to three new cards. You review the
offer at `/deck-builder:campfire`, where you can also prune cards nobody's
touched. And `/deck-builder:ascend` lets you dial up how strictly the repo's
own hooks enforce lint, tests, and coverage as the project matures.

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
/deck-builder:map        # show run state + deck-health stats
/deck-builder:campfire   # resolve a pending reward, or review the deck for pruning
/deck-builder:ascend     # raise or lower the ascension tier (A0-A20)
```

<sub>Developing locally? `claude --plugin-dir ./` loads it without a marketplace,
and `claude plugin validate` checks the manifest.</sub>

### The reward loop (optional)

Card offers are judged by a small Python script (`scripts/curator.py`) using
the [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python).
It's an **optional soft dependency** — without it, everything else in the
plugin works identically, the reward loop just stays quiet:

```
pip install claude-agent-sdk
```

## What gets dealt

```
your-repo/
├── CLAUDE.md                       # relics: rules & conventions for the class
└── .claude/
    ├── deck.json                   # the save file
    ├── settings.json               # only once you /deck-builder:ascend past A0
    ├── deck-builder-ascension.json # ascend's config (tier + lint/test commands)
    ├── deck-builder-state.json     # ephemeral Stop-hook bookkeeping
    ├── deck-pending-reward.json    # a card offer awaiting a /campfire decision
    ├── deck-builder/                # self-contained helpers a dealt card's own
    │   ├── record_play.py           #   hooks call - keep working with no
    │   └── ascension_gate.py        #   engine/plugin installed at all
    └── skills/                     # cards: skills dealt from the class starter deck
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
runs and share one `deck.json`. Each class also declares a `lint`/`test`
command (used by `/deck-builder:ascend`) — `null` where no command is
universal enough to enforce automatically.

## The reward loop

A `Stop` hook (`scripts/reward_gate.py`) fires after every turn but does
almost nothing most of the time: only a new commit, or enough tool-call
activity, makes it worth asking the curator anything at all. When it does ask,
`scripts/curator.py` judges strictly by house rules — **default to skip**;
offer only for a pattern that's genuinely repeated; past a ~12-card soft cap,
every offer must name a card to trade away. An offer is never sprung on you
mid-task: it's detected at `Stop` and surfaced quietly at your next session
start, or whenever you run `/deck-builder:campfire`.

## The ascension ladder

`/deck-builder:ascend` raises how strictly your *own* dealt hooks enforce
quality, by rewriting your repo's `.claude/settings.json` (merging in just its
own entry — anything else already there stays untouched):

| Tier | Enforcement |
|---|---|
| **A0** | hooks warn only (no blocking) |
| **A5** | block the Stop if lint fails |
| **A10** | A5, plus block if tests fail |
| **A15** | A10, plus block on a coverage regression (best-effort — only when a coverage number can actually be parsed from test output) |
| **A20** | A15, plus every room gets a reward-curator review instead of a sampled subset |

Ascension only ever moves when you ask — never automatically.

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
rewards — a lean deck is a strong deck. `/deck-builder:map` now also runs
`deck.py stats` for a deterministic read: total plays, the most-played card,
which cards are unplayed (prune candidates), and the reward take rate.

---

## Status & roadmap

**Act 1 — the starter deck (shipped).** `/deck-builder` init, deterministic
`scan.py`, 5 classes, `deck.json`, and `/deck-builder:map`.

**Act 2 — the engine (shipped).** The `Stop`-hook reward loop
(`reward_gate.py` + `curator.py`), per-card play tracking via skill-scoped
hooks, and `/deck-builder:campfire` for accepting/skipping offers and pruning
via the `deck-curator` agent.

**Act 3 — ascension (shipped).** The A0–A20 strictness ladder
(`/deck-builder:ascend`), ascension shown in the session-start status line,
and `deck.py stats` for deck-health numbers.

**The Heart — community (planned).** Card packs, community classes, and deck
export.

## Contributing

The contribution surface is markdown and YAML — new **classes** and **card
packs**, not Python. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE).
