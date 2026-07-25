# Room-prior + `?` resolution contract

Backend contract for adaptive map events. **Sensors first, model second, player always chooses the node.**

## Goals

1. Make the dungeon feel like *this* repo (bugs when tests fail, features when roadmap is hot).
2. Never autopilot the user’s next task — only weight what a `?` *might* become.
3. Stay fail-open: if AI is down, sensors alone still produce a prior.

## Pipeline

```
repo sensors (deterministic)
        │
        ▼
 pressure_vector: {feature, bug, refactor, design, docs, infra, orient}
        │
        ├─ optional: cheap model re-ranks with one-line rationales
        │
        ▼
 map generator places nodes; `?` nodes store weighted outcome table
        │
        ▼
 player enters `?`
        │
        ▼
 resolve(seed, weights, pools) → concrete room | event | shop | trap
```

## Sensor inputs (v0)

All paths relative to project root. Pure stdlib / git. No network required.

| Sensor ID | Signal | Bumps |
| --- | --- | --- |
| `tests_failing` | Last known test command non-zero (ascension config or class default) | `bug` |
| `coverage_drop` | Parsed coverage < baseline (if known) | `bug`, `refactor` |
| `todo_density` | Count of `TODO`/`FIXME`/`XXX` in diff or tracked files (capped walk) | `feature`, `refactor` |
| `open_wip` | Dirty git + large uncommitted diff | `feature` or `bug` from diff heuristics |
| `diff_test_churn` | High churn in `tests/` without src | `refactor`, `docs` |
| `diff_src_no_tests` | Src churn, no test churn | `bug` (debt), `feature` |
| `infra_files_touched` | Dockerfile/tf/compose in diff | `infra` |
| `no_deck_or_orient` | Missing orientation notes / Colorless class / floor 0 | `orient` |
| `ascension_block` | Recent gate block reason | matching type (`bug` if test, etc.) |
| `pack_gap` | Deck lacks tags the prior wants | shop weight later |

Each sensor emits `{id, room_type_deltas: {type: float}, evidence: str}`.

## Pressure vector

```json
{
  "schema_version": 1,
  "generated_at": "ISO-8601",
  "floor": 3,
  "weights": {
    "feature": 0.28,
    "bug": 0.34,
    "refactor": 0.14,
    "design": 0.08,
    "docs": 0.06,
    "infra": 0.05,
    "orient": 0.05
  },
  "evidence": [
    {"sensor": "tests_failing", "detail": "pytest exit 1", "delta": {"bug": 0.4}}
  ],
  "model": null
}
```

Rules:

- Start from uniform or class-biased prior (e.g. Ironclad → infra↑).
- Apply sensor deltas; clamp each type ≥ 0; renormalize to sum 1.
- If all zero, default `{orient: 1}`.
- **Model step (optional):** may multiply weights by ≥0 factors and attach `rationale`, but may not invent types outside the enum. On failure → `model: null`, keep sensor vector.

## Map placement

When generating / refreshing a floor:

| Node kind | How prior is used |
| --- | --- |
| Fixed fight / elite / boss | Template defines type; prior does not override bosses |
| Campfire / shop | Template cadence (e.g. shop every N) |
| `?` | Store `outcome_table` derived from weights (below) |

### `?` outcome table

```json
{
  "node_id": "f3-q2",
  "kind": "unknown",
  "seed": "abc123",
  "outcomes": [
    {"weight": 0.34, "resolve": "combat", "room_type": "bug", "pool": "monsters_bug"},
    {"weight": 0.22, "resolve": "combat", "room_type": "feature", "pool": "monsters_feature"},
    {"weight": 0.12, "resolve": "combat", "room_type": "refactor", "pool": "elites_refactor"},
    {"weight": 0.10, "resolve": "event", "pool": "events_design"},
    {"weight": 0.08, "resolve": "event", "pool": "events_trap_scope"},
    {"weight": 0.08, "resolve": "shop", "pool": "shop_default"},
    {"weight": 0.06, "resolve": "event", "pool": "events_orient"}
  ]
}
```

Construction recipe (deterministic):

1. Take top 3 room types from pressure vector → combat outcomes (weights proportional).
2. Always reserve small mass for `events_trap_scope` (scope creep) and class-flavor event.
3. If `bug` or `refactor` high and shop not visited this act → bump shop.
4. Renormalize.
5. Freeze `seed` at node creation so re-entering doesn’t reroll (enter once).

## Resolution API (engine-facing)

```
resolve_unknown(node_id, save, prior=None) -> RoomInstance | EventInstance | ShopInstance
```

- Uses frozen `outcome_table` + `seed` (not live prior) so the map doesn’t gaslight the player.
- Prior influences **generation**, not **re-resolution**.
- Returns instance conforming to [content-schema.md](content-schema.md).

## AI curator prompt contract (when used)

Input: pressure vector JSON + bounded evidence strings + deck summary (card names, unplayed) + last N rooms.  
Output JSON schema:

```json
{
  "weights": {"feature": 0, "bug": 0, "refactor": 0, "design": 0, "docs": 0, "infra": 0, "orient": 0},
  "rationale": "one sentence",
  "suggested_intents": [{"room_type": "bug", "intent": "failing auth test will block ship"}]
}
```

House rules: prefer sensor-aligned bumps; never zero out all combat; default toward skip of new cards still lives in reward loop, not here.

## Single-task enforcement

Entering any node sets `save.active_room = instance_id`. Client + engine reject starting another room until `clear | flee | abandon`. Flee returns to map with streak penalty (spec in GDD; numeric v0: `clean_room_streak = 0`).

## Non-goals for this contract

- Autopicking the next node for the user  
- Generating arbitrary natural-language “tickets” with no pool id  
- Calling models on every keystroke (prior refresh: on map open, room clear, or manual refresh)
