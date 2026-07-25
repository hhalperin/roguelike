---
description: Neow's blessing — scan this repo, detect its class, and deal it a starter deck of Claude config (CLAUDE.md relics + .claude/skills cards) tracked in .spire/deck.json. Run once to start a run.
disable-model-invocation: true
allowed-tools: Bash(python3 "${CLAUDE_SKILL_DIR}/../../scripts/scan.py" *), Bash(python3 "${CLAUDE_SKILL_DIR}/../../scripts/deck.py" *)
---

# /spire — Neow's blessing

Deal this project a starter deck: detect its **class** (archetype) and write a
matching set of Claude config into the repo, tracked in a `.spire/deck.json`
save file.

**Paths** (already substituted for you):
- Engine scripts: `${CLAUDE_SKILL_DIR}/../../scripts/` (i.e. `scan.py`, `deck.py`)
- Class data: `${CLAUDE_SKILL_DIR}/../../classes/`
- Target repo (the save file lives here): `${CLAUDE_PROJECT_DIR}` — the project
  you're working in; `/spire` always decks this project.
- Run home: `${CLAUDE_PROJECT_DIR}/.spire/` (deck + bookkeeping + dealt helpers)
- Agent cards: `${CLAUDE_PROJECT_DIR}/.claude/skills/` (where Claude loads them)

## Steps

1. **Guard against re-dealing.** If `${CLAUDE_PROJECT_DIR}/.spire/deck.json`
   already exists (or a legacy `${CLAUDE_PROJECT_DIR}/.claude/deck.json` that
   `deck.py` will migrate), do **not** re-deal. Run
   `python3 "${CLAUDE_SKILL_DIR}/../../scripts/deck.py" show --path "${CLAUDE_PROJECT_DIR}"`,
   show the result, and tell the user to use `/spire:map` to view the run
   or `/spire:campfire` to change cards. Stop here.

2. **Scan.** Run:
   `python3 "${CLAUDE_SKILL_DIR}/../../scripts/scan.py" "${CLAUDE_PROJECT_DIR}"`
   It prints JSON with `primary`, `classes`, `families`, and `monorepo`.

3. **Pick the class(es).**
   - Normally deal the `primary` class.
   - If `monorepo` is `true`, this is a **dual-class run**: deal the two
     strongest classes across different families (e.g. `defect` + `silent`).
   - Read the matching class file(s):
     `${CLAUDE_SKILL_DIR}/../../classes/<class>.yaml`.

4. **Create the save file.** Run
   `python3 "${CLAUDE_SKILL_DIR}/../../scripts/deck.py" init --path "${CLAUDE_PROJECT_DIR}" --class <primary> [--class <secondary>]`.

5. **Deal relics → CLAUDE.md.** For each relic in the class file(s), add its
   `rule` as a bullet under a `## spire relics` heading in
   `${CLAUDE_PROJECT_DIR}/CLAUDE.md`. In a dual-class run, de-duplicate relics by
   `id`. If `CLAUDE.md` already exists, **append** the section (read first, don't
   overwrite). If a legacy `## deck-builder relics` section already exists, append
   new bullets there instead of creating a second heading. Record each with
   `python3 "${CLAUDE_SKILL_DIR}/../../scripts/deck.py" add-relic --path "${CLAUDE_PROJECT_DIR}" --id <relic-id>`.

6. **Deal the play-tracking helper.** Copy
   `${CLAUDE_SKILL_DIR}/../../scripts/record_play.py` to
   `${CLAUDE_PROJECT_DIR}/.spire/bin/record_play.py` verbatim (create
   the directory if needed). This file is intentionally self-contained — it
   keeps working even if the spire plugin is later uninstalled, because
   the save file must not depend on the engine that dealt it.

7. **Deal cards → skills.** Gather the cards from the class file(s). In a
   dual-class run, **de-duplicate by card name** — if both classes define a card
   with the same name (e.g. `run-tests`), deal it once, keeping the primary
   class's version. This keeps the dealt `SKILL.md` files in sync with the deck,
   which `deck.py add-card` also de-duplicates by name.

   For each unique card, create
   `${CLAUDE_PROJECT_DIR}/.claude/skills/<card-name>/SKILL.md` with this exact
   shape (frontmatter from the card's `description`, body from the card's
   `body`, and a **skill-scoped Stop hook** that credits a play whenever this
   card was active — this is what makes `plays`/`last_played` in `deck.json`
   real instead of always zero):

   ```
   ---
   description: <card.description>
   hooks:
     Stop:
       - matcher: "*"
         hooks:
           - type: command
             command: python3 "${CLAUDE_PROJECT_DIR}/.spire/bin/record_play.py" --name <card-name>
   ---
   <card.body>
   ```

   Then record it:
   `python3 "${CLAUDE_SKILL_DIR}/../../scripts/deck.py" add-card --path "${CLAUDE_PROJECT_DIR}" --name <card-name> --type skill --floor 0`.

8. **Deal powers → deck.json.** For each power in the class file(s), record it
   with
   `python3 "${CLAUDE_SKILL_DIR}/../../scripts/deck.py" add-power --path "${CLAUDE_PROJECT_DIR}" --event <event> --name <power-name>`.
   De-duplicate by `(event, name)` across dual-class runs (deck.py already
   no-ops duplicates). Powers are tracked on the run; do **not** rewrite
   `.claude/settings.json` here — ascension owns gate hooks, and optional
   power wiring is a later choice. Mention each power's `description` in the
   blessing summary so the player knows what it means.

9. **Bless the run.** Finish by running
   `python3 "${CLAUDE_SKILL_DIR}/../../scripts/deck.py" show --path "${CLAUDE_PROJECT_DIR}"`
   and present a short, in-theme summary: the class dealt, the relics, cards,
   and powers, plus a nudge that new cards are earned by clearing rooms
   (shipping real work) and that `/spire:shop` can draw from card packs.

## House rules

- **Deterministic before generative:** trust `scan.py` for detection; only use
  judgment to break ties or choose monorepo classes.
- **Don't overwrite the user's work:** append to an existing `CLAUDE.md`, and
  never clobber a card the user already has.
- Keep the starter deck small. More cards are *earned*, not front-loaded.
- **Run vs agent dirs:** `.spire/` holds run knowledge; `.claude/skills/` holds
  cards the agent loads. Don't put skills inside `.spire/`.
