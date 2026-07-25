# Template — facet format

Copy to `formats/<facet>.md` when adding a surface.

## Facet name

**Mode purpose:** one sentence.  
**Player question this screen answers:** …  
**Primary action (exactly one):** …  
**Forbidden on this screen:** …

## Layout (regions)

```
┌─────────────────────────────────────────┐
│ chrome                                  │
├─────────────────────────────────────────┤
│ HERO                                    │
│                                         │
├──────────────────┬──────────────────────┤
│ SECONDARY        │ SUPPORTING           │
├──────────────────┴──────────────────────┤
│ ACTIONS                                 │
└─────────────────────────────────────────┘
```

Describe each region: content types, max items, empty states.

## Type & accent

- Facet accent token: `--facet-…`
- Display label: e.g. `MAP`
- Body hierarchy: …

## Interaction rules

1. …
2. …

## Motion

- Enter: …
- Success: …
- Cancel / back: …

## Copy voice

Examples of good / bad microcopy.

## Content bindings

Which schema fields populate which regions (link `content-schema.md`).

## Wireframe

`wireframes/<facet>.html`

## Do / Don’t

| Do | Don’t |
| --- | --- |
| … | … |
