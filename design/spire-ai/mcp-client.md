# MCP client (Cursor app UI)

The Spire **game client** is an MCP app with UI. The plugin/engine remains source of truth for save I/O and card execution. The client is the HUD + turn director.

## Responsibilities

| Client | Engine / plugin |
| --- | --- |
| Render map, hand, intents, animations | Own `.spire/` save, deck mutations |
| Enforce one active room in UX | Enforce one active room in data |
| Call room-prior + resolve_unknown | Provide sensors / pack list / deck stats |
| Ask agent to “play card X” | Deal skills, run gates, record plays |
| Campfire / shop flows | `deck.py` / pack deal paths |

## Screens (v0 demo)

1. **Title / Continue** — load save or start climb template  
2. **Map** — nodes (combat, `?`, campfire, shop, boss); show act, floor, streak  
3. **Room — Intent** — enemy/event art + intent text + acceptance criteria  
4. **Room — Combat** — hand, energy, play log, “end turn / run acceptance”  
5. **Reward** — up to 3 cards + skip (default focused)  
6. **Campfire** — prune / upgrade / rest  
7. **Shop** — pack cards with prices in abstract gold (or “focus tokens”)  
8. **Ascension select** — pre-run or between acts  

## Turn protocol

```
Client                         Engine                      Agent
  |-- get_save() -------------->|                           |
  |-- get_prior() ------------->|                           |
  |-- refresh_map() ----------->|                           |
  |-- enter_node(id) ---------->| active_room set           |
  |-- show intent --------------|                           |
  |-- play_card(card_id) ------>| validate legal            |
  |                             |-- invoke skill/effect --->|
  |-- run_acceptance() -------->| command / checks          |
  |-- clear_room() ------------>| floor++, reward pending   |
  |-- show_reward / skip ------>| mark_taken/skipped         |
```

### Tool surface (MCP tools draft)

| Tool | Returns |
| --- | --- |
| `spire_get_run` | save + game block |
| `spire_get_prior` | pressure vector |
| `spire_map_refresh` | nodes + frozen `?` tables |
| `spire_enter_node` | room/event/shop instance |
| `spire_list_hand` | legal cards for active room |
| `spire_play_card` | result + new energy |
| `spire_run_acceptance` | pass/fail + log tail |
| `spire_clear_or_flee` | map state |
| `spire_reward_resolve` | take/skip ids |
| `spire_campfire` | prune/upgrade/rest |
| `spire_shop_list` / `spire_shop_buy` | pack offers |

All tools fail-open with structured errors; never brick the IDE.

## Entertainment requirements (focus compliance)

Minimum delight bar for “one task at a time” to stick:

- Intent appears **before** hand is usable  
- Card play has a 200–400ms confirm animation  
- Clear fanfare distinct from flee  
- Reward screen defaults highlight **Skip**  
- Map shows only reachable nodes; active room banner until exit  

No slot-machine dark patterns on rewards.

## Single-task UX rules

- Global “Start new room” disabled while `active_room != null`  
- External agent chats can still happen, but client banner: “Room active: Flaky Suite — finish or flee”  
- Flee confirmation: lose streak + maybe gain curse *Hesitation* (optional v0)

## Visual tone

Readable HUD > purple glow sludge. Think deckbuilder clarity: map graph, intent bar, hand row, energy pips. Class colors subtle (Defect/Silent/Ironclad/Watcher/Colorless).

## Security

- MCP tools only touch project dir + engine scripts  
- No exfil of repo content to third parties beyond user’s model provider  
- Acceptance commands from content must be allowlisted or equal to class `commands.*` / user-confirmed  

## Demo success criteria

A stranger who never played Spire can:

1. Open the MCP app  
2. Understand they pick one map node  
3. Beat one bug room by playing a test card + running acceptance  
4. Skip a reward  
5. See the floor tick  

If that loop isn’t fun, stop and fix entertainment before adding packs.
