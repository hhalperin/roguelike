# Spire design system (v0)

Shared tokens and rules. Facet formats may **specialize** these; they may not invent a second type scale or a glow stack.

## North-star look

Deckbuilder clarity, not dashboard chrome and not generic AI purple.

- Ink on paper (warm off-white, charcoal)
- One accent at a time (facet accent or class accent — not both competing)
- Geometry over gradients; soft noise optional later
- Motion: 2–3 intentional beats per facet max

## Color tokens

```css
--spire-paper: #f3efe6;
--spire-ink: #1c1916;
--spire-muted: #6b645c;
--spire-line: #c9c1b4;
--spire-panel: #ebe4d8;
--spire-danger: #8f2d2d;
--spire-safe: #2f5d3a;
--spire-focus: #1c1916; /* primary CTA = solid ink, not neon */

/* Class accents — sparse use (pip, map node ring, title chip) */
--class-defect: #3a5f7a;    /* cool steel */
--class-silent: #4a6741;    /* quiet green */
--class-ironclad: #8a4b2e;  /* iron rust */
--class-watcher: #5c4d7a;   /* dusk violet — sparingly */
--class-colorless: #6b645c; /* muted */

/* Facet accents — identify the mode at a glance */
--facet-map: #3a5f7a;
--facet-intent: #8a4b2e;
--facet-combat: #8f2d2d;
--facet-reward: #2f5d3a;
--facet-campfire: #9c5527;
--facet-shop: #5c4d7a;
--facet-ascension: #1c1916;
--facet-event: #4a6741;
```

**Rules**

- Any accent used as a fill behind small text must clear 4.5:1 against
  `--spire-paper`. Campfire was `#a65d2e` and measured 4.33:1 under the facet
  tab, so it is `#9c5527` (4.89:1). Accents that only ever carry large text or
  act as borders are exempt.
- Accents used *as* small text need their own darker variant rather than reuse
  of the fill value. See `--safe-text`, `--gold-text`, `--campfire-text` in the
  demo stylesheet.
- Never purple-on-white gradient theme. Watcher violet is an accent pip only.
- Never make Skip look disabled. On Reward, Skip is the visual default.
- Danger only for flee / fail / curse — not for primary navigation.

## Typography

Wireframe / v0 UI may use system stack; product UI should pick **one display + one body** (not Inter/Roboto/Arial as brand). Suggested direction:

- Display: condensed grotesque or slab for titles (“MAP”, “CAMPFIRE”)
- Body: readable serif or humanist sans for intents and card text
- Mono: acceptance commands, sensor evidence

Scale:

| Token | Size | Use |
| --- | --- | --- |
| `display` | 32–40 | Facet title |
| `title` | 22–24 | Room / enemy name |
| `body` | 15–16 | Intent, descriptions |
| `caption` | 12–13 | Meta (floor, act, energy) |
| `mono` | 13 | Commands |

## Spacing & layout chrome

- App shell max width ~1080px inside IDE panel; map may go full width.
- 8px grid. Panels: 12–16px padding.
- Top chrome always: Act · Floor · Class chip · Energy (if in room) · active-room banner.
- Bottom: facet-specific (hand / choices / CTAs) — never duplicate primary CTA top and bottom.

## Motion budget

| Beat | Duration | Where |
| --- | --- | --- |
| Card commit | 200–400ms | Combat |
| Intent reveal | 300ms fade/slide | Intent |
| Room clear | 500–700ms | Combat → Reward |
| Skip settle | 200ms | Reward |
| Map node select | 150ms | Map |

No continuous particle glow. No slot-machine reward roll.

## Components (shared)

- **Node** — map circle/diamond by kind  
- **Card** — title, cost pip, 2–3 lines body, rarity notch  
- **Intent bar** — telegraph + plain-language consequence  
- **Energy pips** — filled/empty  
- **Banner** — active room lock  
- **CTA solid** / **CTA ghost** / **CTA danger**

## Accessibility

- Contrast ≥ WCAG AA on paper/ink  
- Focus rings on all controls (ink outline, 2px)  
- Don’t convey room kind by color alone — shape + label  
- Animations respect `prefers-reduced-motion`

## Facet specialization rule

Each format doc may set:

1. **Hero region** (what owns the first viewport)  
2. **Primary action** (exactly one)  
3. **Forbidden chrome** (e.g. no hand on Map)  
4. **Copy voice** (imperative, terse, in-world)

If two facets share the same hero region pattern, merge them — they’re not distinct enough.
