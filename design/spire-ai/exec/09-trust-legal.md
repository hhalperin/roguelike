# 09 — Trust, safety, and legal

**Status:** living  
**Owner:** founder  
**Decides:** Trust boundaries; open legal questions.

## Problem

A product that writes into repos and sits on coding agents will be judged on trust as hard as on fun. We need explicit boundaries and a short list of legal open questions — not a full compliance program yet.

## Recommendation

### Trust principles

| Principle | Practice |
| :-- | :-- |
| **User-confirmed acceptance** | Acceptance / deal commands are allowlisted and user-confirmed — no silent “just write it” |
| **No silent repo writes beyond deal paths** | Engine writes stay on documented deal/clear/reward paths; no background mutation of user code |
| **Opt-in telemetry only** | Habit metrics for product learning are opt-in; default is local save file only |
| **Never ship code contents in telemetry** | Floors, takes/skips, ascension — not source, secrets, or prompts |
| **IP posture on packs** | Authored packs are product content; contributor license TBD before external pack PRs |
| **Not a PM that owns your backlog** | Messaging and product refuse sprint-board ownership ([non-goals](../non-goals.md)) |
| **Player agency on `?` nodes** | AI may weight priors; player always chooses the path |

### Safety posture (product)

- One active room reduces blast radius of agent action.
- Skip is first-class — users can refuse bad rooms without fighting the tool.
- Ascension / stricter gates are chosen by the player, not forced silently.

### Open legal questions

| Question | Why it matters | Status |
| :-- | :-- | :-- |
| **Trademark “Spire” / “Spire AI”** | Crowded word; clearance before heavy spend on brand | Open — counsel / search |
| **Game-likeness disclaimer vs Slay the Spire** | Inspiration is intentional; avoid implying affiliation with MegaCrit / STS | Open — decide public attribution language |
| **Plugin store / marketplace ToS** | Distribution constraints on Cursor / Claude plugin surfaces | Open — review before Stage 2 launch |
| **Pack contributor license** | Needed before external content PRs | Open — draft after Stage 2 |
| **Privacy policy for opt-in telemetry** | Required if any cloud metrics ship | Deferred until telemetry exists |

### What we are not claiming

- We do not claim to replace human review, security audit, or legal advice on generated code.
- We do not claim affiliation with Slay the Spire or its publishers unless a real partnership exists.

## Open decisions

- [ ] Public STS inspiration wording for landing / README
- [ ] Engage trademark search before Stage 2 landing brand lock
- [ ] Contributor LICENSE snippet for `packs/`

## Links

- [non-goals](../non-goals.md) · [Metrics](08-success-metrics.md) · [Vision](01-vision-category.md)
