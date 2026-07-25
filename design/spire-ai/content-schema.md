# Content schema (v0)

Authoring shapes for cards, enemies, rooms, events, packs, and save extensions.
YAML for humans; JSON OK for machine exports. Engine plugin today uses YAML packs/classes;
game client should accept the same fields.

## Enums

```
room_type: feature | bug | refactor | design | docs | infra | orient
rarity: common | uncommon | rare
card_kind: skill | tactic | power | relic  # relic usually not in hand
enemy_tier: monster | elite | boss
resolve_kind: combat | event | shop | campfire | treasure
```

## Card

```yaml
id: characterization-test
name: Characterization Test
kind: skill
rarity: uncommon
cost: 1                    # energy
room_types: [refactor, bug]  # legal hand filter; empty = any
tags: [testing, safe]
description: Pin current behavior before changing untested code.
play:
  agent_skill: characterization-test   # maps to dealt SKILL.md name when present
  effects:
    - type: require_tests
    - type: open_editor_hint
      paths: ["**/*"]
upgrade:                   # campfire upgrade path (optional)
  cost: 0
  description: Also adds a regression note to the PR body.
```

Rules:

- `play.agent_skill` optional — pure UX cards allowed (e.g. Cut Scope).
- Hand filter: card legal if `room_types` empty or intersects active room type.
- Soft deck cap still ~12 skills that map to agent skills (tactics may be exempt later).

## Relic

```yaml
id: coverage-floor
name: Coverage Floor
rule: Never let coverage drop below its current value without documenting why.
ascension_min: 0
```

## Power (hook)

```yaml
id: ruff-on-edit
event: PostToolUse
name: ruff-on-edit
description: After editing Python files, run ruff on touched paths.
```

## Enemy

```yaml
id: flaky-suite
name: Flaky Suite
tier: elite
room_types: [bug]
hp: 30                     # abstract; UI meter — not real HP accounting required in v0
intent_pool:
  - id: red-then-green
    text: Will fail CI randomly if ignored
    telegraph: "CI roulette"
  - id: quarantine-temptation
    text: Offers a skip-test potion that applies a curse
attacks:
  - id: flake
    damage: 8
    meaning: Re-run fails without code change
rewards:
  card_chance: 0.6
  pack_bias: [testing-discipline]
```

Bosses add `act: 1|2|3` and `must_clear: true`.

## Room instance (runtime)

```json
{
  "id": "f3-q2-resolved",
  "floor": 3,
  "resolve": "combat",
  "room_type": "bug",
  "enemy_id": "flaky-suite",
  "intent_id": "red-then-green",
  "acceptance": {
    "type": "command",
    "cmd": "python -m pytest -q",
    "expect": "exit_0"
  },
  "title": "Flaky Suite",
  "flavor": "It passed on your machine. It won't on CI."
}
```

Acceptance types v0: `command`, `file_exists`, `decision_recorded`, `manual_confirm`.

## Event

```yaml
id: scope-creep-just-one-more
pool: events_trap_scope
name: Just One More Requirement
text: A stakeholder adds a “tiny” must-have. What do you do?
choices:
  - id: take
    label: Accept scope
    effects:
      - type: add_curse_card
        card: bloated-scope
      - type: bump_prior
        room_type: feature
  - id: cut
    label: Cut scope (play Cut Scope if owned)
    effects:
      - type: require_card
        card: cut-scope
      - type: heal_energy
        amount: 1
  - id: defer
    label: Park in backlog
    effects:
      - type: log_room
        note: deferred-scope
```

## Pack

Same as today’s `packs/<name>/pack.yaml`, plus optional game fields:

```yaml
pack: testing-discipline
name: Testing Discipline
description: Keep the suite honest.
room_bias: [bug, refactor]
relics: [...]
cards: [...]
enemies: []      # optional content expansion
events: []
```

## Save extensions (additive on `.spire/deck.json`)

Keep v1 deck fields; game client may add:

```json
{
  "schema_version": 1,
  "game": {
    "act": 1,
    "map_seed": "...",
    "active_room": null,
    "energy_max": 3,
    "hand_size": 5,
    "nodes_cleared": [],
    "curses": [],
    "prior_cache": null
  }
}
```

Plugin without game client ignores `game` safely.

## Pools index

`content/pools.json` (future) maps pool ids → lists of content ids:

```json
{
  "monsters_bug": ["nit-cluster", "regen-bug", "off-by-one"],
  "elites_refactor": ["duplication-hydra", "flaky-suite"],
  "events_trap_scope": ["scope-creep-just-one-more"],
  "shop_default": ["testing-discipline"]
}
```

v0 demo can hardcode pools in one Act template file instead.
