# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Open-source project files: SECURITY, CODE_OF_CONDUCT, ARCHITECTURE, AGENTS, CHANGELOG, packs/, GitHub issue and PR templates, a CI workflow, and repo hygiene configs.
- GitHub best-practice scaffolding: CODEOWNERS, Dependabot, a Python 3.9/3.12 CI matrix, a pre-commit job enforcing the existing .pre-commit-config.yaml, and an optional claude plugin validate CI job.
- Project-level .claude/settings.json: a safe read-only/test/lint permissions allowlist and a non-blocking PostToolUse ruff hook.

## [0.1.0] - 2026-07-24

### Added
- Act 1 (MVP): /deck-builder deals a class-based starter deck, a deterministic scan.py stack detector, five class archetypes, a deck.json save file, and /deck-builder:map.
