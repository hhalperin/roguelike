#!/usr/bin/env python3
"""deck-builder :: deck.py — the save-file (deck.json) manager.

Reads, writes, and validates ``<repo>/.claude/deck.json`` — the roguelike save
file that lives *with the target project*, not with the plugin. Standard library
only. All mutations go through here so the schema stays consistent and writes
stay atomic; the ``/deck-builder`` and ``/deck-builder:map`` skills shell out to
this script rather than editing the JSON directly.

Subcommands
-----------
    init          create a new deck.json for a detected class (idempotent)
    add-card      record a dealt card (skill/relic/power) in the deck
    add-relic     record a relic (a CLAUDE.md rule) in the deck
    add-power     record a power (a hook) in the deck
    remove-card   remove a card (campfire prune / curator-recommended trade)
    remove-relic  remove a relic
    record-play   credit a play to a card (name, plays++, last_played=today)
    mark-offered  bump rewards.offered (by --count, default 1)
    mark-taken    bump rewards.taken (by --count, default 1)
    mark-skipped  bump rewards.skipped (by --count, default 1)
    show          render human-readable run state (backs /deck-builder:map)
    stats         aggregate deck-health stats (plays, unplayed, reward rate)
    validate      check the deck.json schema; exit non-zero if invalid

Examples
--------
    python deck.py init --path . --class defect
    python deck.py add-card --path . --name add-endpoint --type skill --floor 0
    python deck.py show --path .
    python deck.py validate --path .
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys

SCHEMA_VERSION = 1

# Engine-side flavor only (not project knowledge): display names for classes.
CLASS_NAMES = {
    "defect": "The Defect",
    "silent": "The Silent",
    "ironclad": "The Ironclad",
    "watcher": "The Watcher",
    "colorless": "The Colorless",
}

CARD_TYPES = ("skill", "relic", "power")


def _today() -> str:
    """Today's date (YYYY-MM-DD). Overridable via DECK_BUILDER_TODAY for tests."""
    override = os.environ.get("DECK_BUILDER_TODAY")
    if override:
        return override
    return datetime.date.today().isoformat()


def deck_path(repo: str) -> str:
    return os.path.join(repo, ".claude", "deck.json")


def skeleton(classes: list[str], floor: int = 0) -> dict:
    """A fresh deck for one or more classes (first is primary)."""
    classes = classes or ["colorless"]
    return {
        "schema_version": SCHEMA_VERSION,
        "class": classes[0],
        "classes": classes,
        "act": 1,
        "floor": floor,
        "ascension": 0,
        "created": _today(),
        "cards": [],
        "relics": [],
        "powers": [],
        "rooms_cleared": [],
        "clean_room_streak": 0,
        "rewards": {"offered": 0, "taken": 0, "skipped": 0},
    }


def load(repo: str) -> dict:
    with open(deck_path(repo), encoding="utf-8") as fh:
        return json.load(fh)


def save(repo: str, deck: dict) -> None:
    """Atomically write deck.json (temp file in the same dir + os.replace)."""
    path = deck_path(repo)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(deck, fh, indent=2)
        fh.write("\n")
    os.replace(tmp, path)


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #

def validate(deck: dict) -> list[str]:
    """Return a list of schema errors (empty list == valid)."""
    errors: list[str] = []

    def want(key: str, types: type | tuple[type, ...]) -> bool:
        if key not in deck:
            errors.append(f"missing key: {key!r}")
            return False
        if not isinstance(deck[key], types):
            errors.append(f"{key!r} must be {types}, got {type(deck[key]).__name__}")
            return False
        return True

    want("class", str)
    want("classes", list)
    # bool is a subclass of int; exclude it explicitly for numeric fields.
    for key in ("act", "floor", "ascension", "clean_room_streak"):
        if want(key, int) and isinstance(deck[key], bool):
            errors.append(f"{key!r} must be an int, not bool")
    for key in ("cards", "relics", "powers", "rooms_cleared"):
        want(key, list)

    if want("rewards", dict):
        for sub in ("offered", "taken", "skipped"):
            val = deck["rewards"].get(sub)
            if not isinstance(val, int) or isinstance(val, bool):
                errors.append(f"rewards.{sub} must be an int")

    raw_cards = deck.get("cards", [])
    for i, card in enumerate(raw_cards if isinstance(raw_cards, list) else []):
        if not isinstance(card, dict):
            errors.append(f"cards[{i}] must be an object")
            continue
        for key, typ in (("name", str), ("type", str), ("added_floor", int), ("plays", int)):
            if key not in card:
                errors.append(f"cards[{i}] missing {key!r}")
            elif not isinstance(card[key], typ) or (typ is int and isinstance(card[key], bool)):
                errors.append(f"cards[{i}].{key} must be {typ.__name__}")
        if "last_played" in card and not isinstance(card["last_played"], (str, type(None))):
            errors.append(f"cards[{i}].last_played must be a string or null")

    raw_powers = deck.get("powers", [])
    for i, power in enumerate(raw_powers if isinstance(raw_powers, list) else []):
        if not isinstance(power, dict) or "event" not in power or "name" not in power:
            errors.append(f"powers[{i}] must be an object with 'event' and 'name'")

    return errors


# --------------------------------------------------------------------------- #
# Subcommands
# --------------------------------------------------------------------------- #

def cmd_init(args: argparse.Namespace) -> int:
    path = deck_path(args.path)
    if os.path.exists(path) and not args.force:
        print(f"deck.py: deck already exists at {path} (use --force to overwrite)", file=sys.stderr)
        return 1
    classes = args.klass or ["colorless"]
    unknown = [c for c in classes if c not in CLASS_NAMES]
    if unknown:
        print(f"deck.py: unknown class(es): {', '.join(unknown)}", file=sys.stderr)
        return 2
    deck = skeleton(classes, floor=args.floor)
    save(args.path, deck)
    label = " + ".join(CLASS_NAMES[c] for c in classes)
    print(f"Dealt a fresh deck for {label} → {path}")
    return 0


def cmd_add_card(args: argparse.Namespace) -> int:
    deck = load(args.path)
    if any(c.get("name") == args.name for c in deck["cards"]):
        print(f"card {args.name!r} already in deck; leaving unchanged")
        return 0
    floor = args.floor if args.floor is not None else deck.get("floor", 0)
    deck["cards"].append({
        "name": args.name,
        "type": args.type,
        "added_floor": floor,
        "plays": 0,
        "last_played": None,
    })
    save(args.path, deck)
    print(f"Added {args.type} card {args.name!r} at floor {floor}")
    return 0


def cmd_add_relic(args: argparse.Namespace) -> int:
    deck = load(args.path)
    if args.id in deck["relics"]:
        print(f"relic {args.id!r} already present; leaving unchanged")
        return 0
    deck["relics"].append(args.id)
    save(args.path, deck)
    print(f"Added relic {args.id!r}")
    return 0


def cmd_add_power(args: argparse.Namespace) -> int:
    deck = load(args.path)
    if any(p.get("event") == args.event and p.get("name") == args.name for p in deck["powers"]):
        print(f"power {args.name!r} on {args.event} already present; leaving unchanged")
        return 0
    deck["powers"].append({"event": args.event, "name": args.name})
    save(args.path, deck)
    print(f"Added power {args.name!r} on {args.event}")
    return 0


def bump_reward(repo: str, field: str, amount: int = 1) -> int:
    """Bump deck['rewards'][field] by amount; returns the new value."""
    d = load(repo)
    d.setdefault("rewards", {"offered": 0, "taken": 0, "skipped": 0})
    d["rewards"][field] = d["rewards"].get(field, 0) + amount
    save(repo, d)
    return d["rewards"][field]


def remove_card(repo: str, name: str) -> bool:
    """Remove a card by name. Returns True if a card was actually removed."""
    d = load(repo)
    before = len(d["cards"])
    d["cards"] = [c for c in d["cards"] if c.get("name") != name]
    if len(d["cards"]) == before:
        return False
    save(repo, d)
    return True


def remove_relic(repo: str, relic_id: str) -> bool:
    """Remove a relic by id. Returns True if a relic was actually removed."""
    d = load(repo)
    if relic_id not in d["relics"]:
        return False
    d["relics"].remove(relic_id)
    save(repo, d)
    return True


def record_play(repo: str, name: str) -> bool:
    """Credit a play to a card. Returns True if the card was found."""
    d = load(repo)
    for c in d["cards"]:
        if c.get("name") == name:
            c["plays"] = c.get("plays", 0) + 1
            c["last_played"] = _today()
            save(repo, d)
            return True
    return False


def cmd_remove_card(args: argparse.Namespace) -> int:
    if remove_card(args.path, args.name):
        print(f"Removed card {args.name!r}")
        return 0
    print(f"card {args.name!r} not found; nothing removed")
    return 1


def cmd_remove_relic(args: argparse.Namespace) -> int:
    if remove_relic(args.path, args.id):
        print(f"Removed relic {args.id!r}")
        return 0
    print(f"relic {args.id!r} not found; nothing removed")
    return 1


def cmd_record_play(args: argparse.Namespace) -> int:
    if record_play(args.path, args.name):
        print(f"Recorded a play for {args.name!r}")
        return 0
    print(f"card {args.name!r} not found; no play recorded", file=sys.stderr)
    return 1


def _cmd_mark(field: str):
    def _cmd(args: argparse.Namespace) -> int:
        new_value = bump_reward(args.path, field, args.count)
        print(f"rewards.{field} = {new_value}")
        return 0
    return _cmd


def cmd_show(args: argparse.Namespace) -> int:
    try:
        deck = load(args.path)
    except FileNotFoundError:
        print("No deck yet. Run /deck-builder to deal a starter deck.", file=sys.stderr)
        return 1

    names = deck.get("classes") or [deck.get("class", "colorless")]
    label = " + ".join(CLASS_NAMES.get(c, c) for c in names)
    lines = [
        "🎴 deck-builder — run state",
        f"Class: {label}   Act {deck.get('act', 1)} · Floor {deck.get('floor', 0)}"
        f" · Ascension {deck.get('ascension', 0)}",
    ]

    cards = deck.get("cards", [])
    lines.append(f"Cards ({len(cards)}):" if cards else "Cards: none")
    for c in cards:
        last = c.get("last_played") or "never"
        lines.append(
            f"  • {c.get('name', '?'):<22} {c.get('type', 'skill'):<6}"
            f" floor {c.get('added_floor', 0):<3} ×{c.get('plays', 0)}  (last: {last})"
        )

    relics = deck.get("relics", [])
    lines.append(f"Relics ({len(relics)}): " + (", ".join(relics) if relics else "none"))

    powers = deck.get("powers", [])
    if powers:
        lines.append("Powers: " + ", ".join(f"{p['name']}@{p['event']}" for p in powers))
    else:
        lines.append("Powers: none")

    cleared = deck.get("rooms_cleared", [])
    lines.append(f"Rooms cleared ({len(cleared)}): " + (", ".join(cleared) if cleared else "none"))

    r = deck.get("rewards", {})
    lines.append(
        f"Rewards: {r.get('offered', 0)} offered / {r.get('taken', 0)} taken"
        f" / {r.get('skipped', 0)} skipped"
    )
    print("\n".join(lines))
    return 0


ASCENSION_LABELS = {
    0: "A0 — warn only", 5: "A5 — lint blocks", 10: "A10 — +tests block",
    15: "A15 — +coverage regression blocks", 20: "A20 — full gate + every-room review",
}


def stats_summary(d: dict) -> dict:
    """Aggregate deck-health numbers, shared by cmd_stats and its tests."""
    cards = d.get("cards", [])
    total_plays = sum(c.get("plays", 0) for c in cards)
    unplayed = [c["name"] for c in cards if c.get("plays", 0) == 0]
    by_plays = sorted(cards, key=lambda c: c.get("plays", 0), reverse=True)
    r = d.get("rewards", {"offered": 0, "taken": 0, "skipped": 0})
    offered = r.get("offered", 0)
    return {
        "card_count": len(cards),
        "relic_count": len(d.get("relics", [])),
        "total_plays": total_plays,
        "most_played": (by_plays[0]["name"], by_plays[0].get("plays", 0)) if by_plays else None,
        "unplayed": unplayed,
        "reward_take_rate": (r.get("taken", 0) / offered) if offered else None,
        "ascension": d.get("ascension", 0),
        "over_soft_cap": len(cards) >= 12,
    }


def cmd_stats(args: argparse.Namespace) -> int:
    try:
        d = load(args.path)
    except FileNotFoundError:
        print("No deck yet. Run /deck-builder to deal a starter deck.", file=sys.stderr)
        return 1

    s = stats_summary(d)
    tier_label = ASCENSION_LABELS.get(s["ascension"], f"A{s['ascension']}")
    lines = [
        "📊 deck-builder — stats",
        f"Ascension: {tier_label}",
        f"Cards: {s['card_count']}"
        + ("  (at/over the ~12-card soft cap)" if s["over_soft_cap"] else ""),
        f"Relics: {s['relic_count']}",
        f"Total plays across all cards: {s['total_plays']}",
    ]
    if s["most_played"]:
        lines.append(f"Most played: {s['most_played'][0]} (×{s['most_played'][1]})")
    lines.append(
        f"Unplayed cards ({len(s['unplayed'])}): " + (", ".join(s["unplayed"]) or "none")
        + ("  — candidates for a campfire prune" if s["unplayed"] else "")
    )
    if s["reward_take_rate"] is None:
        lines.append("Reward take rate: no rewards offered yet")
    else:
        lines.append(f"Reward take rate: {s['reward_take_rate']:.0%}")
    print("\n".join(lines))
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    try:
        deck = load(args.path)
    except FileNotFoundError:
        print(f"deck.py: no deck.json at {deck_path(args.path)}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"deck.py: deck.json is not valid JSON: {exc}", file=sys.stderr)
        return 1

    errors = validate(deck)
    if errors:
        print("deck.json is INVALID:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    print("deck.json is valid.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="deck.py", description="Manage a repo's deck.json save file."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def add_path(p: argparse.ArgumentParser) -> None:
        p.add_argument("--path", default=".", help="target repo root (default: .)")

    p_init = sub.add_parser("init", help="create a new deck.json")
    add_path(p_init)
    p_init.add_argument("--class", dest="klass", action="append", metavar="CLASS",
                        help="class to deal (repeatable; first is primary)")
    p_init.add_argument("--floor", type=int, default=0, help="starting floor (default: 0)")
    p_init.add_argument("--force", action="store_true", help="overwrite an existing deck")
    p_init.set_defaults(func=cmd_init)

    p_card = sub.add_parser("add-card", help="record a dealt card")
    add_path(p_card)
    p_card.add_argument("--name", required=True)
    p_card.add_argument("--type", choices=CARD_TYPES, default="skill")
    p_card.add_argument("--floor", type=int, default=None,
                        help="floor added (default: current floor)")
    p_card.set_defaults(func=cmd_add_card)

    p_relic = sub.add_parser("add-relic", help="record a relic")
    add_path(p_relic)
    p_relic.add_argument("--id", required=True)
    p_relic.set_defaults(func=cmd_add_relic)

    p_power = sub.add_parser("add-power", help="record a power (hook)")
    add_path(p_power)
    p_power.add_argument("--event", required=True)
    p_power.add_argument("--name", required=True)
    p_power.set_defaults(func=cmd_add_power)

    p_rm_card = sub.add_parser("remove-card", help="remove a card")
    add_path(p_rm_card)
    p_rm_card.add_argument("--name", required=True)
    p_rm_card.set_defaults(func=cmd_remove_card)

    p_rm_relic = sub.add_parser("remove-relic", help="remove a relic")
    add_path(p_rm_relic)
    p_rm_relic.add_argument("--id", required=True)
    p_rm_relic.set_defaults(func=cmd_remove_relic)

    p_play = sub.add_parser("record-play", help="credit a play to a card")
    add_path(p_play)
    p_play.add_argument("--name", required=True)
    p_play.set_defaults(func=cmd_record_play)

    for field in ("offered", "taken", "skipped"):
        p_mark = sub.add_parser(f"mark-{field}", help=f"bump rewards.{field}")
        add_path(p_mark)
        p_mark.add_argument("--count", type=int, default=1)
        p_mark.set_defaults(func=_cmd_mark(field))

    p_show = sub.add_parser("show", help="render run state")
    add_path(p_show)
    p_show.set_defaults(func=cmd_show)

    p_stats = sub.add_parser("stats", help="show aggregate deck-health stats")
    add_path(p_stats)
    p_stats.set_defaults(func=cmd_stats)

    p_val = sub.add_parser("validate", help="validate the deck.json schema")
    add_path(p_val)
    p_val.set_defaults(func=cmd_validate)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except FileNotFoundError as exc:
        print(f"deck.py: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
