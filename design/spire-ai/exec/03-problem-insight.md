# 03 — Problem / insight memo

**Status:** living  
**Owner:** founder  
**Audience:** investors, advisors, hiring — half page.

## Problem

Agent-assisted development already has powerful models and IDEs. What it lacks is **run structure**: people drown in static config, parallel threads, and “what should I do next?” while the real work — the SDLC climb — goes unplayed as a coherent session.

## Insight

1. **Static agent config rots.** Skills, rules, and hooks accumulate like an unused card collection. Without a loop that deals, plays, and retires them, the junk drawer wins.
2. **SDLC is already a climb.** Spec → implement → test → review → ship has floors, elites, and bosses. We are not inventing work; we are framing it.
3. **Entertainment buys single-task discipline.** Points-as-product fails; a *fun loop* (map, room, reward, skip) makes “one active room” stick.
4. **AI weights `?`, player chooses path.** Models are good at priors over foggy nodes; they are bad at owning your backlog. Agency stays with the player.

## Product implication

Ship a **roguelike session layer** on top of existing coding agents:

- **Deck** = lean agent capabilities (cards / relics / powers)
- **Rooms** = real repo work with clear/skip
- **Save** = `.spire/` in the project (truth in the repo)
- **Client** = one-room MCP UI so the climb is playable, not wiki-shaped

Near-term proof: five external testers clear and skip Ship-the-stub without a Spire wiki ([metrics](08-success-metrics.md), [wedge Stage 2](../wedge.md)).

## One-liner

> Spire turns agent-assisted development into a climb you play — one room at a time — so config stays lean and AI advises the map while you choose the path.

## Open decisions

- [ ] Whether hiring narrative leads with “game systems” or “AI tooling” (recommend: game systems for product roles; AI tooling for distribution partners)

## Links

- [GDD](../GDD.md) · [Vision](01-vision-category.md) · [ICP](02-icp-jtbd.md)
