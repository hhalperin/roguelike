# AGENTS.md

Guidance for AI coding agents working in this repository. This mirrors
[`CLAUDE.md`](CLAUDE.md) for tools that read the cross-agent `AGENTS.md`
convention; when the two ever differ, `CLAUDE.md` wins for Claude Code.

## What this repo is

The **game engine** for the `spire` Claude Code plugin. It holds rules,
classes, and scripts — and **zero project knowledge**. What the plugin learns
about a project is written *into that project*, never stored here. See
[ARCHITECTURE.md](ARCHITECTURE.md).

## Rules of the road

- **Scripts are pure standard library.** `scripts/scan.py` and `scripts/deck.py`
  import only the stdlib — no third-party runtime dependencies, no network.
- **Classes are data.** Archetypes live in `classes/*.yaml`; the scripts do not
  parse them (the `/spire` skill does). New archetypes and card packs are
  the intended contribution surface — markdown and YAML, not Python.
- **Deterministic before generative.** `scan.py` detects, `deck.py` validates;
  reserve model judgment for choosing classes and assembling cards.
- **Portable paths only.** In skills, reference bundled files via
  `${CLAUDE_SKILL_DIR}` and the target repo via `${CLAUDE_PROJECT_DIR}` — never
  hardcode absolute or install-specific paths.
- **Don't clobber user work.** Appending beats overwriting; `deck.py init` refuses
  to re-deal over an existing `deck.json`.
- **Run vs agent dirs.** `.spire/` holds run knowledge (save, bookkeeping,
  dealt helpers). `.claude/skills/` holds cards the agent loads. Don't put
  skills inside `.spire/`.

## Checks before you commit

```bash
python3 -m pytest tests/          # scan + deck + class-schema + manifest tests
ruff check scripts/ tests/        # lint (matches the repo's ruff-strict relic)
claude plugin validate .          # manifest + skill frontmatter (needs the CLI)
```
