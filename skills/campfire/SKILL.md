---
description: The campfire — resolve a pending card reward (accept or skip), or when none is pending, review the deck for cards worth pruning. Use to upgrade or trim a deck-builder run.
disable-model-invocation: true
allowed-tools: Bash(python3 "${CLAUDE_SKILL_DIR}/../../scripts/deck.py" *), Read, Write, Edit
---

# /deck-builder:campfire

A deliberate pause: resolve any pending reward, or review the deck for prune
candidates. Never front-load cards here — this is upkeep, not shopping.

**Paths** (already substituted):
- `deck.py`: `${CLAUDE_SKILL_DIR}/../../scripts/deck.py`
- Class data: `${CLAUDE_SKILL_DIR}/../../classes/`
- Target repo: `${CLAUDE_PROJECT_DIR}`
- Pending reward file: `${CLAUDE_PROJECT_DIR}/.claude/deck-pending-reward.json`

## Step 1 — check for a pending reward

Read `${CLAUDE_PROJECT_DIR}/.claude/deck-pending-reward.json`.

### If it exists (a reward is pending)

1. Present the offer(s) plainly: each card's `name`, `type`, `description`,
   and `rationale` from the file, plus its `reason` and any `remove`
   suggestions. Ask the user, per card: accept or skip.
2. **For each accepted card**, deal it exactly as `/deck-builder` step 7 does:
   create `${CLAUDE_PROJECT_DIR}/.claude/skills/<name>/SKILL.md` (frontmatter
   `description` from the offer, a skill-scoped Stop hook calling
   `.claude/deck-builder/record_play.py --name <name>`, and a short body you
   write from the offer's `description`/`rationale`), then record it with
   `deck.py add-card --path "${CLAUDE_PROJECT_DIR}" --name <name> --type <type>`.
   If `.claude/deck-builder/record_play.py` doesn't exist yet in this repo,
   copy it from `${CLAUDE_SKILL_DIR}/../../scripts/record_play.py` first.
3. If the offer named cards to `remove` and the user accepted the trade,
   confirm which ones with the user before removing anything, then run
   `deck.py remove-card --path "${CLAUDE_PROJECT_DIR}" --name <name>` for each
   confirmed removal. Never remove a card the user didn't explicitly confirm.
4. Record the outcome: `deck.py mark-taken --path "${CLAUDE_PROJECT_DIR}"` once
   per accepted card, `deck.py mark-skipped --path "${CLAUDE_PROJECT_DIR}"`
   once per skipped card.
5. Delete `.claude/deck-pending-reward.json` — it's been resolved either way.
6. Show the result with `deck.py show --path "${CLAUDE_PROJECT_DIR}"`.

### If no pending reward exists

1. Read `${CLAUDE_PROJECT_DIR}/.claude/deck.json`.
2. Invoke the **deck-curator** agent for a general review, telling it in your
   prompt: the exact `deck.json` path (`${CLAUDE_PROJECT_DIR}/.claude/deck.json`),
   the exact `deck.py` path above, and the deck's current `cards` (with their
   `plays`/`added_floor`/`last_played`) and `relics`. Ask it which cards (if
   any) look safe to prune.
3. Present its recommendation. If the user confirms a removal, run
   `deck.py remove-card` (or `remove-relic`) for exactly what they confirmed —
   never remove anything they didn't explicitly agree to.
4. If nothing is pruned, say so plainly; a campfire with no changes is a
   perfectly good outcome.

## House rules

- **Never auto-apply.** Every accept/skip/remove needs the user's explicit
  confirmation — campfire proposes, the user decides.
- **Don't front-load.** This is not a second `/deck-builder` — no new cards
  beyond what a pending reward or the curator's judgment already surfaced.
