# Spire AI — design kit

Living contracts for building **Spire AI**: video games for building software with AI.

The Claude Code plugin in this repo is the **engine wedge**. These docs define the
full product: game loop, map/`?` backend, content schemas, and MCP app UI — so
implementation can stay aligned without re-deriving the ideology each time.

| Doc | Use when |
| --- | --- |
| [GDD.md](GDD.md) | North star, loop, win/lose, player fantasy |
| [glossary.md](glossary.md) | Shared language (works for Spire-new readers) |
| [room-prior-contract.md](room-prior-contract.md) | Sensors → weights → `?` resolution (backend) |
| [content-schema.md](content-schema.md) | Cards, enemies, rooms, packs, save extensions |
| [mcp-client.md](mcp-client.md) | Cursor MCP app UI surfaces + turn protocol |
| [wedge.md](wedge.md) | Build order: plugin → demo Act → company |
| [non-goals.md](non-goals.md) | What we refuse so the game stays a game |
| [act-templates/ship-the-stub.md](act-templates/ship-the-stub.md) | Stage 2 vertical demo outline |
| [fixtures/pressure-vector.example.json](fixtures/pressure-vector.example.json) | Example prior payload |
| [ui/](ui/README.md) | Per-facet formats, design system, HTML wireframes |
| [exec/](exec/README.md) | Who buys, why now, how we win, what we measure, what we fund |

**One-line pitch:** Your project is the run. Your agent config is the deck. Spire is the game.

**Discipline pitch:** One room at a time. Entertainment pays for focus. AI weights the dungeon; the player still picks the path.

**Working agreement:** Ideology change → update GDD + non-goals in the same PR. `?` behavior change → update room-prior-contract + fixture. Exec ideology changes must update GDD/non-goals in the same change set ([exec working rules](exec/README.md)).
