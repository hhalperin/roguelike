# Format — Combat

**Mode purpose:** Play a limited hand against one room until acceptance passes.  
**Player question:** “What do I play with the energy I have?”  
**Primary action:** Play a card (or Run acceptance when ready).  
**Forbidden:** Opening another room, shopping, pruning deck mid-fight.

## Layout

```
┌─────────────────────────────────────────┐
│ chrome: energy pips · room HP/meter     │
├─────────────────────────────────────────┤
│ HERO: enemy status + current intent     │
│ log (last 3 plays)                      │
├─────────────────────────────────────────┤
│ HAND (fan / row) — legal cards only     │
│ cost pips on cards                      │
├─────────────────────────────────────────┤
│ [ Run acceptance ]  ghost: End turn     │
│ text link: Flee                         │
└─────────────────────────────────────────┘
```

Hero = **enemy state**. Hand is secondary but always visible. Primary CTA is **Run acceptance** once the player believes the room is clear — not “ask AI to finish.”

## Accent

`--facet-combat`. Card highlight uses ink focus ring.

## Interaction

1. Illegal cards (wrong `room_types`) hidden or greyed with reason.  
2. Play card → 200–400ms commit → engine/agent effect → log line.  
3. Run acceptance → show mono log tail; on pass → clear fanfare → Reward.  
4. Energy 0 → can still Run acceptance or End turn (draw/rules TBD v0: just wait).  

## Motion

Card commit + clear fanfare only. No damage number fireworks spam.

## Do / Don’t

| Do | Don’t |
| --- | --- |
| Filter hand to room | Show entire deck |
| One enemy focus | Split view of backlog |
| Acceptance as win | “Chat until done” as win |
