# Card packs

A **card pack** is a themed, class-agnostic set of cards (skills) — and
optionally relics — that any repo can draw from beyond its class starter deck.
Packs are the modding scene: pure markdown and YAML, no engine code.

> **Status:** packs are a Heart-phase feature. This directory documents the
> format so authors can start now; the loader that *deals* a pack ships with a
> later act. Today, a pack is a proposal and a data file.

## Format

A pack lives at `packs/<pack-name>/pack.yaml`:

```yaml
pack: testing-discipline
name: Testing Discipline
description: Cards that keep a test suite honest.
relics:
  - id: coverage-floor
    rule: "Never let coverage drop below its current value."
cards:
  - name: characterization-test
    description: "Write a characterization test before refactoring untested code."
    body: |
      # Characterization test
      1. Capture current behavior with a test before changing anything.
      2. Refactor.
      3. Confirm the test still passes.
```

The `cards` and `relics` blocks are **identical in shape** to those in
`classes/*.yaml`, so a pack card and a class card are authored the same way.

## Contributing a pack

1. Copy the `cards`/`relics` from an existing class as a model (see `../classes/`).
2. Keep it small and sharp — a handful of high-value cards beats a pile.
3. Open a **"Class or card pack proposal"** issue, or a PR adding `packs/<name>/`.

See [CONTRIBUTING.md](../CONTRIBUTING.md) for the full modding guide.
