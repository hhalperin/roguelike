---
description: The shop — draw optional cards or relics from a community card pack into this run. Use when you want themed extras beyond the class starter deck or a pending reward.
disable-model-invocation: true
allowed-tools: Bash(python3 "${CLAUDE_SKILL_DIR}/../../scripts/pack.py" *), Bash(python3 "${CLAUDE_SKILL_DIR}/../../scripts/deck.py" *), Read, Write, Edit
---

# /spire:shop — draw from a card pack

A deliberate purchase, not a room reward. Packs are class-agnostic themed sets
under the plugin's `packs/` directory. Keep the deck lean — skip is always
valid.

**Paths** (already substituted):
- `pack.py`: `${CLAUDE_SKILL_DIR}/../../scripts/pack.py`
- `deck.py`: `${CLAUDE_SKILL_DIR}/../../scripts/deck.py`
- Target repo: `${CLAUDE_PROJECT_DIR}`
- Play helper: `${CLAUDE_PROJECT_DIR}/.spire/bin/record_play.py`

## Steps

1. **Require a run.** If `${CLAUDE_PROJECT_DIR}/.spire/deck.json` is missing,
   tell the user to run `/spire` first and stop.

2. **List packs.** Run
   `python3 "${CLAUDE_SKILL_DIR}/../../scripts/pack.py" list --json`
   and present the pack names. If none exist, say so and stop.

3. **Ask which pack.** Do not default — the user picks one (or skip).

4. **Read the pack.** Resolve the file with
   `python3 "${CLAUDE_SKILL_DIR}/../../scripts/pack.py" path <name>`,
   then Read that `pack.yaml`. Present its `description`, each relic (`id` +
   `rule`), and each card (`name` + `description`). Soft-cap reminder: past
   ~12 cards, every take should name a removal.

5. **Ask what to take.** The user may accept zero or more relics/cards (prefer
   at most 2 cards). Confirm any trade-away removals explicitly.

6. **Deal accepts.**
   - Relics: append the `rule` under `## spire relics` in
     `${CLAUDE_PROJECT_DIR}/CLAUDE.md` (or a legacy `## deck-builder relics`
     section if that's what exists), then
     `deck.py add-relic --path "${CLAUDE_PROJECT_DIR}" --id <id>`.
   - Cards: deal exactly as `/spire` step 7 —
     `${CLAUDE_PROJECT_DIR}/.claude/skills/<name>/SKILL.md` with a skill-scoped
     Stop hook calling `.spire/bin/record_play.py --name <name>`, then
     `deck.py add-card --path "${CLAUDE_PROJECT_DIR}" --name <name> --type skill`.
     Copy `record_play.py` into `.spire/bin/` first if missing.
   - Removals the user confirmed:
     `deck.py remove-card` / `remove-relic` for each.

7. **Show** `deck.py show --path "${CLAUDE_PROJECT_DIR}"`.

## House rules

- **Never auto-apply.** Shop proposes; the user decides.
- **Lean deck.** Default recommendation is take nothing.
- **Don't invent pack content.** Only deal what the pack.yaml defines.
