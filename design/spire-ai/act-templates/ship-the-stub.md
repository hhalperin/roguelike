# Act template — Ship the stub (Stage 2 demo)

Single-act climb for the first MCP client demo. Author numbers, not lore essays.

## Meta

- **id:** `ship-the-stub`
- **acts:** 1
- **energy_max:** 3
- **hand_size:** 5
- **map:** 8–10 nodes including 2× `?`, 1 campfire, 1 shop, 1 boss

## Map sketch (left → right)

```
[orient]──[?]──[bug]──[campfire]──[feature]──[?]──[shop]──[elite]──[boss: launch-stub]
```

## Starter deck (Colorless + shared)

Cards (names only — full YAML in content later):

- Orient  
- Cut Scope  
- Write the Failing Test  
- Characterization Test  
- Small Diff  
- Run Acceptance  
- Ask for Intent (reveal)  
- Flee with Notes  

Relics: `small-diffs`  
Powers: none required for demo  

## Enemy roster (ids)

Monsters: `nit-cluster`, `regen-bug`, `missing-test`, `dependency-bump`  
Elite: `flaky-suite`  
Boss: `launch-stub` — acceptance: tests pass + README run instructions exist + player confirms “shipable stub”

## Event pools

- `events_orient`: first-room only if class Colorless or floor 0  
- `events_trap_scope`: `scope-creep-just-one-more`  
- `events_design`: `pick-one-entrypoint`  

## `?` recipe

Use [room-prior-contract.md](../room-prior-contract.md) with sensors only. Boss node never becomes `?`.

## Demo script (for testers)

1. Continue run → see map  
2. Clear orient or first bug  
3. Enter `?` → observe it became something plausible  
4. Play two cards → run acceptance  
5. Skip reward  
6. Reach campfire OR note single-room banner works  

## Exit criteria

See [wedge.md](../wedge.md) Stage 2.
