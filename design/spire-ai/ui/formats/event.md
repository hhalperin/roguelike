# Format — Event

**Mode purpose:** A non-combat choice with tradeoffs (design fork, scope trap, orient).  
**Player question:** “Which tradeoff do I accept?”  
**Primary action:** Pick exactly one choice.  
**Forbidden:** Playing the combat hand, multi-select, deferring without a choice id.

## Layout

```
┌─────────────────────────────────────────┐
│ chrome                                  │
├─────────────────────────────────────────┤
│ HERO: event title + short narrative     │
│ (max ~60 words)                         │
├─────────────────────────────────────────┤
│ CHOICES (2–3 stacked buttons)           │
│   label + one-line consequence preview  │
├─────────────────────────────────────────┤
│ caption: this still counts as the room  │
└─────────────────────────────────────────┘
```

Hero = **story prompt**. Choices are the whole action surface — no separate CTA bar.

## Accent

`--facet-event`. Trap events may use danger on the greedy choice only.

## Interaction

1. One click resolves; confirm only if curse applied.  
2. Choice effects must map to schema (`effects[]`).  
3. Returns to Map (or Reward if event grants cards).

## Copy voice

- Good: “Accept scope — gain Bloated Scope curse.”  
- Bad: “Synergize stakeholder alignment outcomes.”

## Do / Don’t

| Do | Don’t |
| --- | --- |
| 2–3 clear choices | 7 radio buttons |
| Preview consequence | Hide the curse |
| Short narrative | Quest log dump |
