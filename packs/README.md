# Card packs

A **card pack** is a themed, class-agnostic set of cards (skills) — and
optionally relics — that any repo can draw from beyond its class starter deck.
Packs are the modding scene: pure markdown and YAML, no engine code.

> **Status:** Heart-phase, first cut. Authors add `packs/<name>/pack.yaml`;
> players draw via `/spire:shop`. `scripts/pack.py` lists packs
> (stdlib — it does not parse YAML); the skill reads the pack file the same
> way `/spire` reads class YAML.

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

## Bundled packs

| Pack | Theme |
|---|---|
| `testing-discipline` | Characterization tests, failing-test-first, regression coverage |

## Contributing a pack

1. Copy the `cards`/`relics` from an existing class or pack as a model.
2. Keep it small and sharp — a handful of high-value cards beats a pile.
3. Open a **"Class or card pack proposal"** issue, or a PR adding `packs/<name>/`.

See [CONTRIBUTING.md](../CONTRIBUTING.md) for the full modding guide.
