# Format — Campfire

**Mode purpose:** Safe rest — prune, upgrade, or rest. No combat.  
**Player question:** “What dead weight do I burn?”  
**Primary action:** Choose one campfire action (Prune default highlight if unplayed cards exist).  
**Forbidden:** Entering another room without leaving, buying from shop, raising ascension here.

## Layout

```
┌─────────────────────────────────────────┐
│ chrome                                  │
├─────────────────────────────────────────┤
│ HERO: campfire mark + “Rest · Prune ·   │
│        Upgrade” mode switcher           │
├─────────────────────────────────────────┤
│ LIST: deck cards with plays · last used │
│ unplayed sorted first                   │
├─────────────────────────────────────────┤
│ [ Confirm prune ]  ghost: Rest only     │
└─────────────────────────────────────────┘
```

Hero = **mode switcher**. List is the work surface. Warm accent — rest, not urgency.

## Accent

`--facet-campfire`.

## Interaction

1. Prune requires explicit confirm; calls engine `remove-card`.  
2. Rest = heal energy flavor + leave to map (v0 may only clear banner).  
3. Upgrade = optional v0 stub.  
4. Never auto-prune.

## Copy voice

- Good: “Unplayed · 0 plays · added floor 1”  
- Bad: “AI selected these cards for deletion.”

## Do / Don’t

| Do | Don’t |
| --- | --- |
| Sort unplayed first | Hide play counts |
| Confirm destructive | Swipe-to-delete without confirm |
| One action per visit (v0) | Full deckbuilder editor |
