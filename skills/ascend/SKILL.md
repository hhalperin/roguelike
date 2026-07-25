---
description: Raise or lower the ascension tier (A0-A20) — how strictly spire's hooks enforce lint/test/coverage in this repo. Manual only; never auto-raises.
disable-model-invocation: true
allowed-tools: Bash(python3 "${CLAUDE_SKILL_DIR}/../../scripts/ascend.py" *), Read, Write
---

# /spire:ascend — the ascension ladder

Raise (or lower) how strictly this repo's dealt hooks enforce quality gates.
**Always manual** — never suggest or apply a change in tier without the user
explicitly choosing one this turn.

**Paths** (already substituted):
- `ascend.py`: `${CLAUDE_SKILL_DIR}/../../scripts/ascend.py`
- `ascension_gate.py` (to deal): `${CLAUDE_SKILL_DIR}/../../scripts/ascension_gate.py`
- Class data: `${CLAUDE_SKILL_DIR}/../../classes/`
- Target repo: `${CLAUDE_PROJECT_DIR}`
- Gate home: `${CLAUDE_PROJECT_DIR}/.spire/bin/ascension_gate.py`
- Gate config: `${CLAUDE_PROJECT_DIR}/.spire/ascension.json`

## Steps

1. **Show the ladder.** Run
   `python3 "${CLAUDE_SKILL_DIR}/../../scripts/ascend.py" show --path "${CLAUDE_PROJECT_DIR}"`.
   If there's no deck yet, tell the user to run `/spire` first and stop.

2. **Ask which tier.** Present the five tiers plainly and ask the user to pick
   one — do not default to "one tier up" without asking. The tiers:
   - **A0** — hooks warn only (no blocking)
   - **A5** — block the Stop if lint fails
   - **A10** — A5, plus block if tests fail
   - **A15** — A10, plus block on a coverage regression (best-effort — only
     enforced when a coverage percentage can actually be parsed from test
     output; otherwise this check silently no-ops rather than blocking on
     data that isn't there)
   - **A20** — A15, plus every room gets a reward-curator review instead of a
     sampled subset

3. **Resolve lint/test commands.** Read `deck.json`'s `classes` list, then read
   each matching `${CLAUDE_SKILL_DIR}/../../classes/<class>.yaml`'s `commands`
   field. In a dual-class run, combine with `&&` (both must pass) — e.g.
   `ruff check . && npm run lint`. If a class's `commands.lint` or
   `commands.test` is `null` (no reliable universal command for that class,
   e.g. Colorless), tell the user which gate can't be enforced automatically
   and will stay warn-only, rather than guessing a command.

4. **Deal the gate script.** If
   `${CLAUDE_PROJECT_DIR}/.spire/bin/ascension_gate.py` doesn't
   already exist, copy it there verbatim from
   `${CLAUDE_SKILL_DIR}/../../scripts/ascension_gate.py` (same
   self-contained/no-engine-dependency reasoning as `record_play.py`).

5. **Apply.** Run
   `python3 "${CLAUDE_SKILL_DIR}/../../scripts/ascend.py" apply --path "${CLAUDE_PROJECT_DIR}" --tier <N> --lint-cmd "<resolved or omit>" --test-cmd "<resolved or omit>"`.
   This merges a Stop hook into the target repo's own `.claude/settings.json`
   — it only ever touches spire's own entry, never anything else
   already there. The hook command points at `.spire/bin/ascension_gate.py`.

6. **Confirm.** Re-run `ascend.py show` and report the new tier plainly,
   including any gate that's staying warn-only for lack of a known command.

## House rules

- **Never auto-raise.** `clean_room_streak` in `deck.json` is tracked for a
  possible future opt-in, but today ascension only moves when a human asks.
- **Honesty over false enforcement.** A gate with no known command warns; it
  never pretends to block on a guessed one.
