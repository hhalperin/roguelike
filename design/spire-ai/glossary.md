# Glossary

Terms for builders and for readers who have never played *Slay the Spire*.

## For everyone

| Term | Meaning |
| --- | --- |
| **Roguelike (here)** | A climb where you start with a small toolkit, face rooms one at a time, get offers after wins, and get stronger by *refusing* most offers. |
| **Run** | One project climb with persistent save state. |
| **Deck** | Your current set of agent skills, rules, and hooks. |
| **Card** | One playable engineering move this turn (costs energy). |
| **Hand** | The subset of cards you may play in *this* room. |
| **Energy** | Budget for the turn (attention/context/time). Empty hand or energy → end turn / resolve. |
| **Room** | Exactly one active task. No second task until you leave. |
| **Map** | The choices of what to do next (nodes). |
| **Intent** | What the room will do to you if ignored or mishandled (shown up front). |
| **Clear** | Room acceptance met (e.g. tests pass, decision written, PR opened). |
| **Skip** | Declining a reward. Skilled play, not failure. |
| **Campfire** | Safe node: prune deck, upgrade a card, rest (no combat). |
| **Shop** | Buy from a pack (themed card set). |
| **Ascension** | Same climb, harder rules (stricter quality gates). |
| **Class** | Play style from repo archetype (Python, TS, infra, ML, unknown). |
| **Pack** | Mod content: extra cards/relics with a theme. |
| **Save file** | `.spire/` in the repo — the run on disk. |
| **Engine** | Rules + scripts (this plugin). Holds no project secrets. |
| **Client** | MCP app UI in Cursor — the animated game HUD. |

## Combat flavors

| Term | Meaning |
| --- | --- |
| **Monster** | Small, local problem (bug, flake, nit cluster). |
| **Elite** | Expensive problem (migration, auth, perf). |
| **Boss** | Act-defining decision or ship gate. |
| **Event** | Non-combat choice with tradeoffs (scope creep trap, spike, design fork). |
| **`?` node** | Unknown until entered; outcome weighted by project pressure. |

## Room types (work kinds)

| Type | Player-facing | Typical clear |
| --- | --- | --- |
| `feature` | Build something new | Acceptance checks / demo path |
| `bug` | Fix something broken | Repro test green |
| `refactor` | Reshape without behavior change | Characterization tests hold |
| `design` | Decide structure | ADR / recorded decision |
| `docs` | Explain | Doc merged / linked from README |
| `infra` | Runtime / deploy / IaC | Plan reviewed / apply gated |
| `orient` | Map unknown terrain | Notes in save + next map reveal |

## Team shorthand

| Term | Meaning |
| --- | --- |
| **Room-prior** | Backend scores for which room types the project needs now. |
| **Pressure vector** | Normalized weights over room types (sum ≈ 1). |
| **Legal cards** | Hand filter: cards tagged for this room type / enemy family. |
| **Wedge** | Shipable slice: today’s plugin → one-act MCP demo → company. |
| **Spire AI** | Company line: games for AI-assisted building. |
