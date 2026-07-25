# Format — Reward

**Mode purpose:** Offer earned cards; make **Skip** the easy, proud default.  
**Player question:** “Do I take something, or keep the deck lean?”  
**Primary action:** Skip.  
**Forbidden:** Forced take, timed offers, burying Skip, opening Shop mid-reward.

## Layout

```
┌─────────────────────────────────────────┐
│ chrome · “Room cleared”                 │
├─────────────────────────────────────────┤
│ HERO: SKIP panel (largest, prefocused)  │
├─────────────────────────────────────────┤
│ OFFERS: up to 3 compact card previews   │
│ (secondary)                             │
├─────────────────────────────────────────┤
│ if over soft-cap: trade-away required   │
│ caption: take/skip run stats            │
└─────────────────────────────────────────┘
```

This format deliberately inverts normal “upgrade shop” UI. **Skip owns the hero region.**

## Accent

`--facet-reward` (safe green) on Skip. Offers use muted panels.

## Interaction

1. Focus lands on Skip.  
2. Take → optional remove if soft-cap; then Map.  
3. No reshuffle / reroll in v0.  
4. Show running take/skip counts (lean pressure).

## Motion

Skip settle 200ms; no card pack opening animation that delays Skip.

## Do / Don’t

| Do | Don’t |
| --- | --- |
| Skip as hero | Skip as tiny text link |
| Max 3 offers | Infinite scroll catalog |
| Soft-cap trade | Silent deck bloat |
