---
description: Rubric for deciding whether a repeated pattern should become a skill, a hook (power), a CLAUDE.md rule (relic), or a subagent — and when to offer nothing at all. Use when considering adding to or changing a repo's Claude config / deck.
when_to_use: When evaluating whether to add a skill, hook, rule, or agent to a repo; when reviewing config bloat; when deciding a card reward at the end of a task.
user-invocable: false
---

# Card evaluation rubric

Use this when you're tempted to add something to a repo's Claude config (its
"deck"). The goal is a small, sharp deck — not a pile of rules.

## House rules (in order)

1. **Default to skip.** Most of the time the right answer is to add nothing. A
   good deck stays lean; a high skip rate is healthy, not a failure.
2. **Repeated only.** Only propose a card for a pattern you have seen **repeat**
   (a workflow done ≥3 times) or a mistake that has **bitten twice**. Never turn
   a one-off into permanent config.
3. **Soft cap ~12 cards.** Past roughly a dozen cards, every addition must come
   with a proposed **removal**. Trade, don't accumulate.
4. **Deterministic before generative.** If a script or an existing tool can
   enforce it, prefer that over a prompt-time instruction.

## Which type of card?

| You want to… | Card type | Where it lives |
| :-- | :-- | :-- |
| Capture a reusable procedure / checklist | **Skill** | `.claude/skills/<name>/SKILL.md` |
| Enforce something automatically every turn | **Power** (hook) | `.claude/settings.json` hooks |
| State a durable rule or boundary | **Relic** (CLAUDE.md rule) | `CLAUDE.md` |
| Delegate a specialized, self-contained job | **Subagent** | `.claude/agents/<name>.md` |

Decision hints:
- Is it a *fact or boundary* ("never commit to main")? → **Relic**.
- Is it a *procedure* you re-run ("scaffold an endpoint with a test")? → **Skill**.
- Must it happen *without being asked*, deterministically (format on save, block
  on failing tests)? → **Power/hook**.
- Is it a *big, separable task* with its own context (a security review)? →
  **Subagent**.
- Is it none of these, or only happened once? → **offer nothing**.

## When offering a reward

Offer at most 3 candidates, and always include **skip** as the honest default.
Say *why* each is justified — name the repeated pattern or the repeated failure.
