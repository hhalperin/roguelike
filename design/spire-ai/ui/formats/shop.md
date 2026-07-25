# Format — Shop

**Mode purpose:** Optional pack draw — deliberate purchase, not a room reward.  
**Player question:** “Do I spend focus on a themed pack card?”  
**Primary action:** Buy (or Leave).  
**Forbidden:** Soft-forcing buys; mixing reward skip UI here; multi-pack cart checkout in v0.

## Layout

```
┌─────────────────────────────────────────┐
│ chrome · focus tokens / gold            │
├─────────────────────────────────────────┤
│ HERO: pack identity (name + blurb)      │
├─────────────────────────────────────────┤
│ GRID: 3–6 wares (card/relic tiles)      │
│ price on each                           │
├─────────────────────────────────────────┤
│ [ Buy selected ]     ghost: Leave shop  │
└─────────────────────────────────────────┘
```

Hero = **pack brand** (like a distinct work-page style per pack later). Grid is catalog; one selection at a time in v0.

## Accent

`--facet-shop`. Pack themes may tint hero subtly; wares stay paper/ink.

## Interaction

1. Select ware → Buy enabled.  
2. Buy → engine deal skill/relic → token debit.  
3. Leave → Map.  
4. Soft-cap warning before buy if over 12.

## Do / Don’t

| Do | Don’t |
| --- | --- |
| Pack as hero identity | Generic “store” |
| Leave always easy | Dark-pattern discount timer |
| Show soft-cap | Infinite buy spam |
