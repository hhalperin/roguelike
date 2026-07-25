# 08 — Success metrics (exec dashboard)

**Status:** living  
**Owner:** founder  
**Decides:** North-star, stage gates, habit metrics — not vanity DAU.

## Problem

Without stage-linked metrics, we will optimize for installs or chat volume instead of “is the climb playable and sticky?”

## Recommendation

### North-star (near-term)

**External players can complete a climb (clear + skip) without a Spire wiki.**

Stage 2 operationalization: **5 external testers** finish Ship-the-stub with clear and skip, using client facets / dealt skills only.

### Metric dictionary

| Metric | Definition | Healthy signal |
| :-- | :-- | :-- |
| **Wiki-free completes** | Testers finish demo climb without reading design kit | Stage 2 gate: 5/5 or 5 recruited with documented fails |
| **Rooms cleared / session** | Clears in a single play session | Rising with fun; flat + frustration = loop issue |
| **Skip rate** | Skips / (clears + skips) | **High is healthy** — lean decks, refuse junk rooms |
| **Active-room violations** | Attempts to work outside the active room / multi-room thrash | **~0** — one-room discipline |
| **Take / skip (opt-in later)** | Reward card take vs skip | Insight into deck bloat pressure |
| **Floor reached (opt-in later)** | Max floor in a run | Climb length / difficulty calibration |
| **Ascension chosen (opt-in later)** | Ascension level selected | Hardcore engagement — never log code contents |

**Never collect:** source code contents, secret values, or raw prompts by default. Telemetry is opt-in only ([09](09-trust-legal.md)).

### Stage-gate table (linked to wedge)

| Stage | Gate (exec) | Notes |
| :-- | :-- | :-- |
| **0–1** | Internal dogfood deal + room clear on engine repo | Engineering readiness |
| **2** | 5 external wiki-free Ship-the-stub completes; demo video shippable | **Only active build milestone to fund now** |
| **3** | MCP client facets cover map → combat → reward without terminal babysitting | Client readiness |
| **4–5** | ≥1 external clear on each of first funded packs/climbs beyond stub | Content moat start |
| **6** | Revisit paid packs/seats decision with usage evidence | Business model unlock |

Full build detail: [wedge.md](../wedge.md).

### Explicit non-metrics (ignore for now)

- Raw DAU / install vanity without completes
- Lines of code generated
- “Agent autonomy” percentage

## Open decisions

- [ ] Opt-in telemetry transport (if any) post–Stage 2
- [ ] Quantitative skip-rate band once 5-tester data exists

## Links

- [wedge](../wedge.md) · [Resourcing](10-resourcing-milestones.md) · [Trust](09-trust-legal.md)
