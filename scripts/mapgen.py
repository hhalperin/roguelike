#!/usr/bin/env python3
"""Deterministic map generation in the shape of Slay the Spire's act maps.

Pure standard library, like every other script here. A map is a function of
(seed, act, ascension), so a run is reproducible and a reviewer can re-derive
any map from its seed.

The rules implemented here are documented in design/spire-ai/sts-fidelity.md.
The short version: walk paths up a grid, then deal room kinds from a shuffled
fixed-quota bag subject to a row rule, a parent rule and a sibling rule, with
monster as the fallback when nothing in the bag is legal.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from dataclasses import dataclass, field
from dataclasses import replace as dc_replace

ROWS = 15
COLS = 7
PATHS = 6

# Forced floors, zero-indexed. StS forces floor 1 to monster, floor 9 to
# treasure and floor 15 to rest.
TREASURE_ROW = 8
NO_REST_ELITE_BEFORE_ROW = 5
MIN_REJOIN_DISTANCE = 3

KINDS = ("monster", "elite", "rest", "shop", "treasure", "unknown")

# Kinds that may not repeat along an edge, and kinds that may not repeat
# between siblings. Monster is exempt from both because it is the fallback an
# over-constrained node lands on.
PARENT_UNIQUE_KINDS = ("rest", "treasure", "shop", "elite")
SIBLING_UNIQUE_KINDS = ("rest", "treasure", "shop", "elite", "unknown")

QUOTAS = {"rest": 0.12, "elite": 0.08, "shop": 0.05, "unknown": 0.22}
ELITE_ASCENSION_MULTIPLIER = 1.6

# Unknown-node resolution. Checked in this order; each base climbs by its own
# value every time it fails to fire, and resets when it fires.
RAMP_ORDER = ("monster", "shop", "treasure")
RAMP_BASE = {"monster": 0.10, "shop": 0.03, "treasure": 0.02}

ACT_SEED_OFFSET = {1: 1, 2: 200, 3: 600}

# The act boss is visible from the first floor, because that is what makes an
# act a plan rather than a survival crawl.
BOSSES = {
    1: (
        {"id": "unclear-requirements", "name": "Unclear Requirements"},
        {"id": "undecided-architecture", "name": "The Undecided Architecture"},
        {"id": "scope-without-a-spec", "name": "Scope Without a Spec"},
    ),
    2: (
        {"id": "integration-boss", "name": "The Integration"},
        {"id": "half-migrated-schema", "name": "The Half-Migrated Schema"},
        {"id": "cross-service-deadline", "name": "Cross-Service Deadline"},
    ),
    3: (
        {"id": "launch", "name": "Launch"},
        {"id": "scale-cliff", "name": "The Scale Cliff"},
        {"id": "compliance-gate", "name": "The Compliance Gate"},
    ),
}


def floor_rng(seed: int, floor: int) -> random.Random:
    """Per-floor isolated RNG.

    StS re-seeds several streams to `seed + floor` on entering a room, so that
    what you did on floor 7 cannot perturb floor 8. That isolation is what lets
    a player reason precisely and a run stay reproducible.
    """
    return random.Random(seed + floor)


@dataclass(frozen=True)
class Node:
    row: int
    col: int
    kind: str = "monster"
    next_cols: tuple[int, ...] = ()

    @property
    def key(self) -> tuple[int, int]:
        return (self.row, self.col)

    @property
    def id(self) -> str:
        return f"r{self.row}c{self.col}"

    def replace(self, **changes: object) -> Node:
        return dc_replace(self, **changes)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "row": self.row,
            "col": self.col,
            "kind": self.kind,
            "next": list(self.next_cols),
        }


@dataclass
class SpireMap:
    seed: int
    act: int
    ascension: int
    nodes: dict[tuple[int, int], Node]
    boss: dict
    rows: int = ROWS
    cols: int = COLS
    _unknown: dict[tuple[int, int], dict] = field(default_factory=dict, repr=False)

    def row_nodes(self, row: int) -> list[Node]:
        return [self.nodes[k] for k in sorted(self.nodes) if k[0] == row]

    def next_nodes(self, node: Node) -> list[Node]:
        return [self.nodes[(node.row + 1, c)] for c in node.next_cols]

    def parents(self, node: Node) -> list[Node]:
        if node.row == 0:
            return []
        return [n for n in self.row_nodes(node.row - 1) if node.col in n.next_cols]

    def siblings(self, node: Node) -> list[Node]:
        out: dict[tuple[int, int], Node] = {}
        for parent in self.parents(node):
            for child in self.next_nodes(parent):
                if child.key != node.key:
                    out[child.key] = child
        return [out[k] for k in sorted(out)]

    def to_dict(self) -> dict:
        return {
            "seed": self.seed,
            "act": self.act,
            "ascension": self.ascension,
            "rows": self.rows,
            "cols": self.cols,
            "boss": dict(self.boss),
            "nodes": [self.nodes[k].to_dict() for k in sorted(self.nodes)],
        }

    def fingerprint(self) -> str:
        blob = json.dumps(self.to_dict(), sort_keys=True).encode()
        return hashlib.sha1(blob).hexdigest()


class Ramp:
    """Per-act miss counters for unknown-node resolution."""

    def __init__(self) -> None:
        self.misses = dict.fromkeys(RAMP_BASE, 0)

    def chance(self, kind: str) -> float:
        return RAMP_BASE[kind] * (self.misses[kind] + 1)

    def miss(self, kind: str) -> None:
        self.misses[kind] += 1

    def fire(self, kind: str) -> None:
        self.misses[kind] = 0


# ---------------------------------------------------------------------------
# path walking
# ---------------------------------------------------------------------------


def _crosses(edges: dict[tuple[int, int], set[int]], row: int, col: int, target: int) -> bool:
    for (r, c), targets in edges.items():
        if r != row or c == col:
            continue
        for t in targets:
            if (col < c and target > t) or (col > c and target < t):
                return True
    return False


def _ancestors(
    parents: dict[tuple[int, int], set[int]], key: tuple[int, int], depth: int
) -> set[tuple[int, int]]:
    seen = {key}
    frontier = {key}
    for _ in range(depth):
        nxt: set[tuple[int, int]] = set()
        for row, col in frontier:
            for pcol in parents.get((row, col), ()):
                nxt.add((row - 1, pcol))
        frontier = nxt - seen
        seen |= nxt
        if not frontier:
            break
    return seen


def _rejoins_too_soon(
    parents: dict[tuple[int, int], set[int]], row: int, col: int, target: int
) -> bool:
    existing = parents.get((row + 1, target), set())
    mine = _ancestors(parents, (row, col), MIN_REJOIN_DISTANCE)
    for other in existing:
        if other == col:
            continue
        if mine & _ancestors(parents, (row, other), MIN_REJOIN_DISTANCE):
            return True
    return False


def _walk_paths(rng: random.Random) -> dict[tuple[int, int], set[int]]:
    edges: dict[tuple[int, int], set[int]] = {}
    parents: dict[tuple[int, int], set[int]] = {}
    first_start: int | None = None

    for path in range(PATHS):
        col = rng.randrange(COLS)
        if path == 1 and col == first_start:
            # Guarantee at least two entrances, as StS does for its second path.
            col = (col + 1 + rng.randrange(COLS - 1)) % COLS
        if path == 0:
            first_start = col

        for row in range(ROWS - 1):
            options = [c for c in (col - 1, col, col + 1) if 0 <= c < COLS]
            rng.shuffle(options)
            legal = [c for c in options if not _crosses(edges, row, col, c)]
            preferred = [c for c in legal if not _rejoins_too_soon(parents, row, col, c)]
            target = (preferred or legal or [col])[0]

            edges.setdefault((row, col), set()).add(target)
            parents.setdefault((row + 1, target), set()).add(col)
            col = target

    return edges


# ---------------------------------------------------------------------------
# room assignment
# ---------------------------------------------------------------------------


def _is_forced_row(row: int) -> bool:
    return row in (0, TREASURE_ROW, ROWS - 1)


def _forced_kind(row: int) -> str:
    if row == 0:
        return "monster"
    if row == TREASURE_ROW:
        return "treasure"
    return "rest"


def _build_bag(rng: random.Random, assignable: int, ascension: int) -> list[str]:
    bag: list[str] = []
    for kind, share in QUOTAS.items():
        if kind == "elite" and ascension >= 1:
            share *= ELITE_ASCENSION_MULTIPLIER
        bag.extend([kind] * round(share * assignable))
    rng.shuffle(bag)
    return bag


def _kind_is_legal(nodes: dict[tuple[int, int], Node], node: Node, kind: str) -> bool:
    if kind in ("rest", "elite") and node.row < NO_REST_ELITE_BEFORE_ROW:
        return False
    if kind == "rest" and node.row >= ROWS - 2:
        return False

    parent_cols = [
        n.col
        for n in nodes.values()
        if n.row == node.row - 1 and node.col in n.next_cols
    ]
    if kind in PARENT_UNIQUE_KINDS:
        for pcol in parent_cols:
            if nodes[(node.row - 1, pcol)].kind == kind:
                return False

    if kind in SIBLING_UNIQUE_KINDS:
        for pcol in parent_cols:
            for sib_col in nodes[(node.row - 1, pcol)].next_cols:
                sib = nodes.get((node.row, sib_col))
                if sib is not None and sib_col != node.col and sib.kind == kind:
                    return False
    return True


def _assign_kinds(
    rng: random.Random, edges: dict[tuple[int, int], set[int]], ascension: int
) -> dict[tuple[int, int], Node]:
    keys = set(edges)
    for (row, _col), targets in edges.items():
        for t in targets:
            keys.add((row + 1, t))

    nodes: dict[tuple[int, int], Node] = {}
    for key in sorted(keys):
        row, col = key
        nodes[key] = Node(
            row=row,
            col=col,
            kind=_forced_kind(row) if _is_forced_row(row) else "monster",
            next_cols=tuple(sorted(edges.get(key, ()))),
        )

    assignable = [k for k in sorted(nodes) if not _is_forced_row(k[0])]
    bag = _build_bag(rng, len(assignable), ascension)

    for key in assignable:
        for i, kind in enumerate(bag):
            if _kind_is_legal(nodes, nodes[key], kind):
                nodes[key] = nodes[key].replace(kind=kind)
                bag.pop(i)
                break
        # No legal kind left in the bag, so the node stays a monster room.

    return nodes


def generate(seed: int, act: int, ascension: int = 0) -> SpireMap:
    """Build the act map for a seed. Pure: same inputs, same map."""
    if act not in ACT_SEED_OFFSET:
        raise ValueError(f"unknown act: {act}")
    rng = random.Random(seed + ACT_SEED_OFFSET[act])
    edges = _walk_paths(rng)
    nodes = _assign_kinds(rng, edges, ascension)
    boss = dict(BOSSES[act][rng.randrange(len(BOSSES[act]))])
    return SpireMap(seed=seed, act=act, ascension=ascension, nodes=nodes, boss=boss)


# ---------------------------------------------------------------------------
# unknown resolution and traversal
# ---------------------------------------------------------------------------


def resolve_unknown(spire_map: SpireMap, node: Node, ramp: Ramp) -> dict:
    """Resolve one unknown node, frozen so re-entering never rerolls."""
    if node.key in spire_map._unknown:
        return spire_map._unknown[node.key]

    rng = floor_rng(spire_map.seed + ACT_SEED_OFFSET[spire_map.act], node.row)
    outcome = "event"
    for kind in RAMP_ORDER:
        if rng.random() < ramp.chance(kind):
            ramp.fire(kind)
            outcome = kind
            break
        ramp.miss(kind)

    result = {"node": node.id, "resolve": outcome}
    spire_map._unknown[node.key] = result
    return result


def legal_moves(spire_map: SpireMap, node: Node | None) -> list[Node]:
    """Any entry is legal to start. After that, only outgoing edges are."""
    if node is None:
        return spire_map.row_nodes(0)
    return spire_map.next_nodes(node)


def is_legal_move(spire_map: SpireMap, frm: Node | None, to: Node) -> bool:
    return any(n.key == to.key for n in legal_moves(spire_map, frm))


# ---------------------------------------------------------------------------
# the lever: a rerunnable invariant check
# ---------------------------------------------------------------------------


def check_invariants(spire_map: SpireMap) -> list[str]:
    """Return a list of violated invariants. Empty means the map is legal."""
    problems: list[str] = []
    m = spire_map

    def fail(msg: str) -> None:
        problems.append(f"seed={m.seed} act={m.act} {msg}")

    if m.rows != ROWS or m.cols != COLS:
        fail(f"grid is {m.rows}x{m.cols}")

    entries = m.row_nodes(0)
    if not entries:
        fail("no entry nodes")
    if len({n.col for n in entries}) < 2:
        fail("fewer than two entrances")
    if any(n.kind != "monster" for n in entries):
        fail("floor 1 is not all monster")
    if any(n.kind != "treasure" for n in m.row_nodes(TREASURE_ROW)):
        fail("treasure floor is not all treasure")
    if any(n.kind != "rest" for n in m.row_nodes(ROWS - 1)):
        fail("pre-boss floor is not all rest")
    if not m.boss.get("name"):
        fail("boss is not named")

    for node in m.nodes.values():
        if node.kind not in KINDS:
            fail(f"unknown kind {node.kind!r} at {node.id}")
        if node.row == ROWS - 1:
            if node.next_cols:
                fail(f"{node.id} on the last row has outgoing edges")
        elif not node.next_cols:
            fail(f"dead end at {node.id}")

        for col in node.next_cols:
            if abs(col - node.col) > 1:
                fail(f"{node.id} steps more than one column")
            if (node.row + 1, col) not in m.nodes:
                fail(f"{node.id} points at a missing node")

        if node.kind in ("rest", "elite") and node.row < NO_REST_ELITE_BEFORE_ROW:
            fail(f"{node.kind} too early at {node.id}")
        if node.kind == "rest" and node.row == ROWS - 2:
            fail(f"rest directly below the pre-boss rest at {node.id}")

        # The parent and sibling rules govern bag dealing. Forced floors are
        # assigned before that step and are uniform by design, so a whole floor
        # of treasure or rest is legal rather than a violation.
        if not _is_forced_row(node.row):
            if node.kind in PARENT_UNIQUE_KINDS:
                for parent in m.parents(node):
                    if parent.kind == node.kind:
                        fail(f"{node.kind} stacked along an edge at {node.id}")
            if node.kind in SIBLING_UNIQUE_KINDS:
                for sib in m.siblings(node):
                    if sib.kind == node.kind and not _is_forced_row(sib.row):
                        fail(f"{node.kind} duplicated between siblings at {node.id}")

    for row in range(ROWS - 1):
        edges = [(n.col, c) for n in m.row_nodes(row) for c in n.next_cols]
        for a_from, a_to in edges:
            for b_from, b_to in edges:
                if a_from < b_from and a_to > b_to:
                    fail(f"crossing edges on row {row}")

    reached: set[tuple[int, int]] = set()
    frontier = list(entries)
    while frontier:
        node = frontier.pop()
        if node.key in reached:
            continue
        reached.add(node.key)
        frontier.extend(m.next_nodes(node))
    if reached != set(m.nodes):
        fail("some nodes are unreachable from an entry")

    return problems


# ---------------------------------------------------------------------------
# cli
# ---------------------------------------------------------------------------

GLYPHS = {
    "monster": "M",
    "elite": "E",
    "rest": "R",
    "shop": "$",
    "treasure": "T",
    "unknown": "?",
}


def render(spire_map: SpireMap) -> str:
    """ASCII map, boss at the top, floor 1 at the bottom."""
    width = spire_map.cols * 4
    lines = [f"  {'BOSS':^{width}}", f"  {spire_map.boss['name']:^{width}}"]
    for row in range(spire_map.rows - 1, -1, -1):
        nodes = {n.col: n for n in spire_map.row_nodes(row)}
        cells = "".join(
            f" {GLYPHS[nodes[c].kind]}  " if c in nodes else "    "
            for c in range(spire_map.cols)
        )
        lines.append(f"{row + 1:>2}{cells}")
        if row:
            links = ["    "] * spire_map.cols
            for node in spire_map.row_nodes(row - 1):
                for target in node.next_cols:
                    # Read top-down: the glyph sits under the upper node and
                    # leans toward the lower node it came from.
                    mark = "|" if target == node.col else ("/" if target > node.col else "\\")
                    if links[target].strip() in ("", mark):
                        links[target] = f" {mark}  "
                    else:
                        links[target] = " *  "
            lines.append(f"  {''.join(links)}")
    legend = "  ".join(f"{g}={k}" for k, g in GLYPHS.items())
    lines.append(f"\n  {legend}")
    return "\n".join(lines)


def _cmd_show(args: argparse.Namespace) -> int:
    spire_map = generate(args.seed, args.act, ascension=args.ascension)
    if args.json:
        print(json.dumps(spire_map.to_dict(), indent=2))
    else:
        print(render(spire_map))
    return 0


def _cmd_emit_js(args: argparse.Namespace) -> int:
    """Emit maps as a plain JS global so the wireframe demo needs no build step.

    Keeps one source of truth: the demo renders what this generator produced
    rather than reimplementing the rules in JavaScript.
    """
    maps = [
        generate(seed, act, ascension=args.ascension).to_dict()
        for seed in range(args.seeds)
        for act in sorted(ACT_SEED_OFFSET)
    ]
    payload = json.dumps(maps, indent=2)
    print("/* Generated by scripts/mapgen.py emit-js. Do not edit by hand. */")
    print(f"window.SPIRE_MAPS = {payload};")
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    problems: list[str] = []
    checked = 0
    for seed in range(args.seeds):
        for act in sorted(ACT_SEED_OFFSET):
            for ascension in (0, 1):
                spire_map = generate(seed, act, ascension=ascension)
                problems.extend(check_invariants(spire_map))
                if generate(seed, act, ascension=ascension).fingerprint() != (
                    spire_map.fingerprint()
                ):
                    problems.append(f"seed={seed} act={act} is not reproducible")
                checked += 1
    if problems:
        for line in problems[: args.limit]:
            print(line)
        print(f"\n{len(problems)} problem(s) across {checked} maps")
        return 1
    print(f"ok: {checked} maps, every invariant holds")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate and check Spire act maps.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    show = sub.add_parser("show", help="render one map")
    show.add_argument("--seed", type=int, default=0)
    show.add_argument("--act", type=int, default=1, choices=sorted(ACT_SEED_OFFSET))
    show.add_argument("--ascension", type=int, default=0)
    show.add_argument("--json", action="store_true")
    show.set_defaults(func=_cmd_show)

    emit = sub.add_parser("emit-js", help="emit maps as a JS global for the demo")
    emit.add_argument("--seeds", type=int, default=4)
    emit.add_argument("--ascension", type=int, default=0)
    emit.set_defaults(func=_cmd_emit_js)

    verify = sub.add_parser("verify", help="check invariants across many seeds")
    verify.add_argument("--seeds", type=int, default=200)
    verify.add_argument("--limit", type=int, default=20)
    verify.set_defaults(func=_cmd_verify)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
