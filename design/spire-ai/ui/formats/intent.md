# Format — Intent

**Mode purpose:** Show what this room will do to you *before* you can play cards.  
**Player question:** “What am I fighting, and what does success mean?”  
**Primary action:** Begin combat / Face event.  
**Forbidden:** Hand interaction, playing cards, skipping acceptance reveal.

## Layout

```
┌─────────────────────────────────────────┐
│ chrome + active-room banner             │
├─────────────────────────────────────────┤
│ HERO: enemy/event portrait + name       │
│ INTENT BAR (telegraph)                  │
│ plain consequence (1–2 sentences)       │
├─────────────────────────────────────────┤
│ ACCEPTANCE panel (mono command / checks)│
├─────────────────────────────────────────┤
│ [ Begin ]           ghost: Flee         │
└─────────────────────────────────────────┘
```

Hero is the **threat + intent**, not the hand. This screen exists so entertainment (drama) buys focus.

## Accent

`--facet-intent`. Danger only on Flee.

## Interaction

1. Begin → Combat or Event; hand locked until this screen is completed.  
2. Flee → confirm → map; streak break.  
3. Acceptance criteria always visible (no surprise win condition).

## Content bindings

`enemy.name`, `intent_pool[].text`, `room.acceptance`, `flavor`.

## Copy voice

- Good: “Will fail CI randomly if ignored.”  
- Bad: “This enemy uses stochastic reliability degradation paradigms.”

## Do / Don’t

| Do | Don’t |
| --- | --- |
| Intent before hand | Jump straight into cards |
| Show clear condition | Hide how to win |
| Short flavor | Lore paragraphs |
