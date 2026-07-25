# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Rebranded the plugin from `deck-builder` to `spire`; commands are now
  `/spire`, `/spire:map`, `/spire:campfire`, and `/spire:ascend`.
- Moved the run home to `.spire/` (`deck.json`, `state.json`,
  `pending-reward.json`, `ascension.json`, `bin/`). Agent primitives
  (skills, settings hooks, CLAUDE.md relics) stay under `.claude/` /
  `CLAUDE.md`. Legacy `.claude/deck.json` layouts migrate automatically.

### Added
- Open-source project files: SECURITY, CODE_OF_CONDUCT, ARCHITECTURE, AGENTS, CHANGELOG, packs/, GitHub issue and PR templates, a CI workflow, and repo hygiene configs.
- GitHub best-practice scaffolding: CODEOWNERS, Dependabot, a Python 3.9/3.12 CI matrix, a pre-commit job enforcing the existing .pre-commit-config.yaml, and an optional claude plugin validate CI job.
- Project-level .claude/settings.json: a safe read-only/test/lint permissions allowlist and a non-blocking PostToolUse ruff hook.
- Act 2 (the engine): a Stop-hook reward loop (reward_gate.py + curator.py using claude-agent-sdk on a cheap model with schema-enforced JSON output), per-card play tracking via skill-scoped Stop hooks (record_play.py), and /spire:campfire (accept/skip a pending reward, or prune via the new deck-curator agent).
- Act 3 (ascension): the A0-A20 ascension ladder via /spire:ascend and ascend.py (merges a Stop hook into the target repo's own .claude/settings.json without touching anything else there), the self-contained ascension_gate.py (lint/test/coverage-regression gate), and deck.py stats for deck-health numbers.
- Per-class lint/test commands in classes/*.yaml, used by the ascension ladder to generate real gate commands (null where no command is universal enough for a class).

## [0.1.0] - 2026-07-24

### Added
- Act 1 (MVP): /deck-builder deals a class-based starter deck, a deterministic scan.py stack detector, five class archetypes, a deck.json save file, and /deck-builder:map.
