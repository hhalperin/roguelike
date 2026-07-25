# Spire AI — Game Design Document (v0)

Status: living · Owner: Spire AI · Last aligned with plugin: Heart (rooms, packs, shop, powers, detection.json)

## Pitch

Spire AI builds **video games for building software with AI**.

The first game is a project-building roguelike: you climb a map of work, play a limited hand of engineering moves, fight bugs and design bosses with visible intents, skip most rewards, prune at campfires, and raise ascension only when you choose.

The AI is a companion that **plays cards inside the rules** — not an unsupervised intern with infinite tabs.

## Player fantasy

> I am climbing my project. I only fight one room at a time. My deck is lean. The dungeon feels like *my* codebase. Skipping is skill.

## Core loop (one turn)

```
Map → pick ONE node → enter room (only legal task)
  → see enemy/event intent
  → play cards from hand (energy-limited)
  → resolve (tests/diff/agent actions)
  → clear / flee / fail
  → reward or campfire beat
  → map again
```

**Hard rule:** only one active room. Entertainment (intent UX, short combat, clear reward beat) is what makes the single-task constraint acceptable.

## Three acts (default climb)

| Act | Name | Fantasy | Typical bosses |
| --- | --- | --- | --- |
| I | Discover | Orient, spike, cut scope | Unclear requirements |
| II | Build | Ship vertical slices | Feature elite → integration boss |
| III | Harden / Ship | Gates, rollback, launch | Launch boss / scale / compliance |

Vertical variants later (MVP climb, enterprise harden, Watcher’s eval climb) swap act skins and pack weights — same engine.

## Mapping (game → software)

| Game | Software |
| --- | --- |
| Run | One project / milestone climb |
| Class | Repo archetype (Defect, Silent, Ironclad, Watcher, Colorless) |
| Card | Playable move (skill / playbook / agent action + cost) |
| Relic | Standing policy (`CLAUDE.md` / always-on rule) |
| Power | Hook (automatic) |
| Energy | Attention / context / time budget this turn |
| Monster | Bug, flake, dependency break, nit cluster |
| Elite | Migration, auth hole, perf cliff, schema knot |
| Boss | Architecture lock, launch, multi-tenant, compliance |
| Room clear | Acceptance for that node (tests green, PR up, decision recorded) |
| Card reward | New skill/relic offer after clear (default skip) |
| Campfire | Retro: upgrade, prune, rest |
| Shop | Pack draw |
| `?` node | Mystery work typed by room-prior backend |
| Ascension | Stricter gates on the same climb |
| Save | `.spire/` in the repo (engine ↔ reality bridge) |

## Win / lose / abandon

- **Win act:** defeat act boss (defined per climb template).
- **Win run:** clear Act III boss (or template equivalent).
- **Lose room:** failed acceptance under ascension rules (can flee with penalty).
- **Abandon run:** always allowed; save persists; no shame UX.
- **Deck death:** soft-cap breach without trades — campfire forced, not hard lock (v0).

## What must stay true

1. Start small; earn cards.
2. Skip is first-class.
3. One room at a time.
4. Deterministic sensors before generative room typing.
5. Game state and engineering state share a save (playing a card does repo work).
6. Ascension is player-chosen.

## Pillars

| Pillar | Means |
| --- | --- |
| Focus | Single active room; hand filtered to room type |
| Agency | Player picks map nodes; AI only weights `?` |
| Legibility | Intents visible before you play |
| Lean | Soft cap, prune, skip default |
| Reality | Cards mutate the real repo / CI / save |

## Out of scope for GDD detail

See [non-goals.md](non-goals.md). Content shapes: [content-schema.md](content-schema.md). Backend `?`: [room-prior-contract.md](room-prior-contract.md). UI: [mcp-client.md](mcp-client.md).
