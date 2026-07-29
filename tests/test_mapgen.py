"""Tests for mapgen.py.

These encode the Slay the Spire map-generation invariants documented in
design/spire-ai/sts-fidelity.md. They are property tests over many seeds
rather than fixtures, because the generator's contract is "every seed produces
a legal map", not "seed 7 produces this map".
"""
import itertools
import json

import mapgen
import pytest

SEEDS = list(range(60))
ACTS = (1, 2, 3, 4, 5)

# Seeds whose walk needed the repair path or a re-walk. A 200-seed sweep called
# these legal for a while, so they are pinned by name.
KNOWN_HARD = ((2520, 5), (1631, 4))

# Generated once. Most tests sweep the whole set, so regenerating per test made
# widening the sweep expensive and kept it too narrow to catch a 1-in-12,000 bug.
_CACHE: dict[int, list] = {}


def all_maps(ascension=0):
    if ascension not in _CACHE:
        _CACHE[ascension] = [
            mapgen.generate(seed, act, ascension=ascension)
            for seed, act in itertools.product(SEEDS, ACTS)
        ]
    return _CACHE[ascension]


# --------------------------------------------------------------------------
# determinism
# --------------------------------------------------------------------------


def test_generate_is_pure():
    for seed, act in itertools.product(range(12), ACTS):
        first = mapgen.generate(seed, act).to_dict()
        second = mapgen.generate(seed, act).to_dict()
        assert first == second


def test_distinct_seeds_mostly_differ():
    shapes = {mapgen.generate(s, 1).fingerprint() for s in range(30)}
    assert len(shapes) > 20


def test_acts_differ_for_one_seed():
    shapes = {mapgen.generate(99, a).fingerprint() for a in ACTS}
    assert len(shapes) == len(ACTS)


# --------------------------------------------------------------------------
# shape and forced floors
# --------------------------------------------------------------------------


def test_dimensions():
    m = mapgen.generate(1, 1)
    assert m.rows == 15
    assert m.cols == 7
    assert all(0 <= n.col < 7 for n in m.nodes.values())
    # 15 climbable floors plus the boss sitting one row above them.
    assert all(0 <= n.row <= mapgen.BOSS_ROW for n in m.nodes.values())


def test_first_floor_is_all_monster():
    for m in all_maps():
        entries = m.row_nodes(0)
        assert entries
        assert all(n.kind == "monster" for n in entries)


def test_treasure_floor_is_all_treasure():
    for m in all_maps():
        row = m.row_nodes(mapgen.TREASURE_ROW)
        assert row
        assert all(n.kind == "treasure" for n in row)


def test_preboss_floor_is_all_rest():
    for m in all_maps():
        row = m.row_nodes(m.rows - 1)
        assert row
        assert all(n.kind == "rest" for n in row)


def test_at_least_two_entrances():
    for m in all_maps():
        assert len({n.col for n in m.row_nodes(0)}) >= 2


def test_boss_is_known_up_front():
    for m in all_maps():
        assert m.boss
        assert m.boss["name"]


# --------------------------------------------------------------------------
# connectivity
# --------------------------------------------------------------------------


def test_every_node_reachable_from_an_entry():
    for m in all_maps():
        seen = set()
        frontier = [n for n in m.row_nodes(0)]
        while frontier:
            node = frontier.pop()
            if node.key in seen:
                continue
            seen.add(node.key)
            frontier.extend(m.next_nodes(node))
        assert seen == set(m.nodes)


def test_every_node_leads_to_the_boss():
    for m in all_maps():
        boss = [n for n in m.nodes.values() if n.kind == "boss"]
        assert len(boss) == 1
        assert boss[0].next_cols == ()
        for node in m.nodes.values():
            if node.kind == "boss":
                continue
            assert node.next_cols, f"dead end at {node.key}"
        # every path converges on the boss
        for node in m.row_nodes(m.rows - 1):
            assert node.next_cols == (boss[0].col,)


def test_a_boss_is_reachable_from_every_entry():
    for m in all_maps():
        boss = next(n for n in m.nodes.values() if n.kind == "boss")
        for entry in m.row_nodes(0):
            seen, frontier = set(), [entry]
            while frontier:
                n = frontier.pop()
                if n.key in seen:
                    continue
                seen.add(n.key)
                frontier.extend(m.next_nodes(n))
            assert boss.key in seen, f"boss unreachable from {entry.id}"


def test_edges_move_exactly_one_row_and_at_most_one_column():
    for m in all_maps():
        for node in m.nodes.values():
            for col in node.next_cols:
                # the final row funnels into the boss from any column
                if node.row != m.rows - 1:
                    assert abs(col - node.col) <= 1
                assert (node.row + 1, col) in m.nodes


def test_no_crossing_edges():
    for m in all_maps():
        for row in range(m.rows - 1):
            edges = [
                (n.col, c) for n in m.row_nodes(row) for c in n.next_cols
            ]
            for (a_from, a_to), (b_from, b_to) in itertools.combinations(edges, 2):
                if a_from < b_from:
                    assert a_to <= b_to, f"crossing edge on row {row}"


# --------------------------------------------------------------------------
# placement rules
# --------------------------------------------------------------------------


def test_no_rest_or_elite_on_early_floors():
    for m in all_maps():
        for row in range(mapgen.NO_REST_ELITE_BEFORE_ROW):
            for node in m.row_nodes(row):
                assert node.kind not in ("rest", "elite")


def test_no_rest_directly_below_the_preboss_rest():
    for m in all_maps():
        for node in m.row_nodes(m.rows - 2):
            assert node.kind != "rest"


def bag_assigned(m):
    """Nodes dealt from the quota bag, i.e. everything off a forced floor.

    Forced floors are uniform by design (all monster, all treasure, all rest),
    so the parent and sibling rules do not apply to them.
    """
    forced = (0, mapgen.TREASURE_ROW, m.rows - 1)
    return [n for n in m.nodes.values() if n.row not in forced]


def test_parent_rule():
    for m in all_maps():
        for node in bag_assigned(m):
            if node.kind not in mapgen.PARENT_UNIQUE_KINDS:
                continue
            for parent in m.parents(node):
                assert parent.kind != node.kind, f"{node.kind} stacked at {node.key}"


def test_sibling_rule():
    for m in all_maps():
        forced = (0, mapgen.TREASURE_ROW, m.rows - 1)
        for node in bag_assigned(m):
            if node.kind not in mapgen.SIBLING_UNIQUE_KINDS:
                continue
            for sibling in m.siblings(node):
                if sibling.row in forced:
                    continue
                assert sibling.kind != node.kind, f"sibling clash at {node.key}"


def test_monster_is_exempt_from_the_sibling_rule():
    """Monster is the fallback for an over-constrained node, so it may repeat.

    Asserted as behaviour: some generated map has two monster siblings. If the
    rules ever covered monster, the generator could not satisfy them.
    """
    found = False
    for m in all_maps():
        for node in bag_assigned(m):
            if node.kind != "monster":
                continue
            if any(s.kind == "monster" for s in m.siblings(node)):
                found = True
                break
        if found:
            break
    assert found, "expected monster siblings somewhere"


def test_ascension_increases_elite_density():
    def elites(ascension):
        return sum(
            1
            for m in all_maps(ascension=ascension)
            for n in m.nodes.values()
            if n.kind == "elite"
        )

    assert elites(1) > elites(0)


def test_every_kind_is_known():
    for m in all_maps():
        assert all(n.kind in mapgen.KINDS for n in m.nodes.values())


# --------------------------------------------------------------------------
# distribution
#
# The first implementation dealt the bag strictly row by row, which let the
# lowest floors consume every shop and unknown before the upper floors were
# reached. Rows 11-14 came out pure monster in 600 of 600 maps. Green tests
# said nothing, because nothing looked at where kinds landed.
# --------------------------------------------------------------------------


def test_variety_reaches_the_top_of_the_map():
    for m in all_maps():
        upper = [n for n in m.nodes.values() if 9 <= n.row <= 13]
        assert {n.kind for n in upper} != {"monster"}, (
            f"seed {m.seed} act {m.act}: floors 10-14 are a monster corridor"
        )


def test_most_floors_offer_a_choice():
    forced = (0, mapgen.TREASURE_ROW, mapgen.ROWS - 1)
    for m in all_maps():
        uniform = sum(
            1
            for row in range(m.rows)
            if row not in forced and len({n.kind for n in m.row_nodes(row)}) == 1
        )
        assert uniform <= 6, f"seed {m.seed} act {m.act}: {uniform} floors with no choice"


def test_shops_and_elites_are_not_confined_to_the_lower_floors():
    rows_with = {"shop": set(), "elite": set()}
    for m in all_maps():
        for n in m.nodes.values():
            if n.kind in rows_with:
                rows_with[n.kind].add(n.row)
    assert max(rows_with["shop"]) >= 9, "shops never appear on the upper half"
    assert max(rows_with["elite"]) >= 9, "elites never appear on the upper half"


def test_quotas_stay_in_the_right_ballpark():
    counts = {"elite": 0, "shop": 0, "unknown": 0, "rest": 0}
    assignable = 0
    forced = (0, mapgen.TREASURE_ROW, mapgen.ROWS - 1)
    for m in all_maps():
        for n in m.nodes.values():
            if n.row in forced or n.kind == "boss":
                continue
            assignable += 1
            if n.kind in counts:
                counts[n.kind] += 1
    for kind, share in mapgen.QUOTAS.items():
        actual = counts[kind] / assignable
        assert share * 0.5 <= actual <= share * 1.6, f"{kind} at {actual:.3f}, wanted ~{share}"


# --------------------------------------------------------------------------
# rejoin rule
# --------------------------------------------------------------------------


def test_branches_do_not_rejoin_one_floor_after_splitting():
    for m in all_maps():
        for node in m.nodes.values():
            if node.row + 2 >= mapgen.BOSS_ROW:
                continue  # converging on the boss is the point
            kids = m.next_nodes(node)
            for i in range(len(kids)):
                for j in range(i + 1, len(kids)):
                    shared = set(kids[i].next_cols) & set(kids[j].next_cols)
                    assert not shared, f"seed {m.seed} act {m.act}: rejoin at {node.id}"


# --------------------------------------------------------------------------
# endless
# --------------------------------------------------------------------------


def test_acts_past_the_heart_keep_generating():
    for act in (5, 9, 40, 200):
        m = mapgen.generate(3, act)
        assert mapgen.check_invariants(m) == []
        assert m.boss["name"]


def test_endless_acts_thicken_the_elites():
    def elites(act):
        return sum(
            1
            for seed in range(25)
            for n in mapgen.generate(seed, act).nodes.values()
            if n.kind == "elite"
        )

    assert elites(20) > elites(4)


def test_endless_acts_have_distinct_maps():
    prints = {mapgen.generate(1, act).fingerprint() for act in range(1, 12)}
    assert len(prints) == 11


def test_act_zero_is_rejected():
    with pytest.raises(ValueError):
        mapgen.generate(1, 0)


def test_seed_and_act_do_not_collide():
    """An additive per-act offset made seed 199 act 1 equal seed 0 act 2."""
    prints = {}
    for seed in range(120):
        for act in range(1, 7):
            fp = mapgen.generate(seed, act).fingerprint()
            assert fp not in prints, f"({seed},{act}) collides with {prints.get(fp)}"
            prints[fp] = (seed, act)


# --------------------------------------------------------------------------
# the checker has to catch a broken map, not just bless a generated one
# --------------------------------------------------------------------------


def test_invariants_catch_a_missing_kind():
    m = mapgen.generate(4, 1)
    for key, node in list(m.nodes.items()):
        if node.kind == "elite":
            m.nodes[key] = node.replace(kind="monster")
    problems = mapgen.check_invariants(m)
    assert any("elite share" in p for p in problems), problems


def test_invariants_catch_a_corridor():
    """A single-lane map has no routing decision, whatever its room mix."""
    nodes = {}
    for row in range(mapgen.ROWS):
        if row == mapgen.TREASURE_ROW:
            kind = "treasure"
        elif row == mapgen.ROWS - 1:
            kind = "rest"
        else:
            kind = "monster"
        nxt = (mapgen.BOSS_COL,) if row == mapgen.ROWS - 1 else (3,)
        nodes[(row, 3)] = mapgen.Node(row=row, col=3, kind=kind, next_cols=nxt)
    nodes[(mapgen.BOSS_ROW, mapgen.BOSS_COL)] = mapgen.Node(
        row=mapgen.BOSS_ROW, col=mapgen.BOSS_COL, kind="boss"
    )
    corridor = mapgen.SpireMap(seed=0, act=1, ascension=0, nodes=nodes, boss={"name": "X"})
    problems = mapgen.check_invariants(corridor)
    assert any("branch point" in p for p in problems), problems
    assert any("no choice" in p for p in problems), problems


def test_check_invariants_never_raises_on_a_malformed_map():
    """It is the artifact a reviewer runs, so it must report rather than crash."""
    m = mapgen.generate(4, 1)
    victim = m.row_nodes(3)[0]
    occupied = {n.col for n in m.row_nodes(4)}
    absent = next(c for c in range(mapgen.COLS) if c not in occupied)
    m.nodes[victim.key] = victim.replace(next_cols=(absent,))
    problems = mapgen.check_invariants(m)
    assert any("missing node" in p for p in problems), problems


def test_generated_maps_have_enough_branch_points():
    for m in all_maps():
        forks = sum(1 for n in m.nodes.values() if len(n.next_cols) > 1)
        assert forks >= 3, f"seed {m.seed} act {m.act} has {forks} branch points"


# --------------------------------------------------------------------------
# unknown resolution
# --------------------------------------------------------------------------


def test_unknown_resolution_is_frozen_per_node():
    m = mapgen.generate(4, 1)
    unknowns = [n for n in m.nodes.values() if n.kind == "unknown"]
    assert unknowns
    node = unknowns[0]
    ramp = mapgen.Ramp()
    first = mapgen.resolve_unknown(m, node, ramp)
    again = mapgen.resolve_unknown(m, node, ramp)
    assert first == again
    assert first["resolve"] in ("monster", "shop", "treasure", "event")


def test_unknown_ramp_climbs_until_it_fires():
    ramp = mapgen.Ramp()
    assert ramp.chance("shop") == mapgen.RAMP_BASE["shop"]
    ramp.miss("shop")
    assert ramp.chance("shop") == mapgen.RAMP_BASE["shop"] * 2
    ramp.fire("shop")
    assert ramp.chance("shop") == mapgen.RAMP_BASE["shop"]


def test_unknown_outcomes_track_the_ramp_over_a_run():
    m = mapgen.generate(11, 2)
    ramp = mapgen.Ramp()
    outcomes = [
        mapgen.resolve_unknown(m, n, ramp)["resolve"]
        for n in m.nodes.values()
        if n.kind == "unknown"
    ]
    assert outcomes
    assert all(o in ("monster", "shop", "treasure", "event") for o in outcomes)


def replay_with_rolls(rolls, ramp):
    """Resolve from exported rolls alone, the way any client must.

    This does not execute demo.js, so it cannot catch the client drifting. What
    it proves is that unknown_rolls exports exactly the values resolve_unknown
    consumes, in order, so a client that applies the exported ramp thresholds
    reaches the same outcome. The thresholds themselves are shipped in
    mapdata.js and asserted by tests/test_mapdata_current.py.
    """
    for i, kind in enumerate(mapgen.RAMP_ORDER):
        if rolls[i] < mapgen.RAMP_BASE[kind] * (ramp.misses[kind] + 1):
            ramp.fire(kind)
            return kind
        ramp.miss(kind)
    return "event"


def test_exported_rolls_reproduce_resolve_unknown():
    for m in all_maps():
        unknowns = [n for n in m.nodes.values() if n.kind == "unknown"]
        engine_ramp = mapgen.Ramp()
        client_ramp = mapgen.Ramp()
        for node in unknowns:
            engine = mapgen.resolve_unknown(m, node, engine_ramp)["resolve"]
            client = replay_with_rolls(m.unknown_rolls(node), client_ramp)
            assert engine == client, f"client drift at {node.id}"


def test_every_unknown_node_exports_its_rolls():
    for m in all_maps():
        for payload in m.to_dict()["nodes"]:
            if payload["kind"] == "unknown":
                assert len(payload["rolls"]) == len(mapgen.RAMP_ORDER)
                assert all(0.0 <= r < 1.0 for r in payload["rolls"])
            else:
                assert "rolls" not in payload


def test_event_is_the_common_unknown_outcome():
    hits = {"event": 0, "monster": 0, "shop": 0, "treasure": 0}
    for seed in range(60):
        m = mapgen.generate(seed, 1)
        ramp = mapgen.Ramp()
        for node in m.nodes.values():
            if node.kind == "unknown":
                hits[mapgen.resolve_unknown(m, node, ramp)["resolve"]] += 1
    assert hits["event"] > hits["monster"] > hits["shop"]


# --------------------------------------------------------------------------
# traversal
# --------------------------------------------------------------------------


def test_any_entry_is_legal_then_only_edges_are():
    m = mapgen.generate(7, 1)
    entries = m.row_nodes(0)
    assert {n.id for n in mapgen.legal_moves(m, None)} == {n.id for n in entries}

    node = entries[0]
    moves = mapgen.legal_moves(m, node)
    assert moves, "an entry must lead somewhere"
    # every move is one row up and joined by an edge
    for move in moves:
        assert move.row == node.row + 1
        assert move.col in node.next_cols
    # and nothing else on that row is legal
    unreachable = [n for n in m.row_nodes(node.row + 1) if n.col not in node.next_cols]
    for n in unreachable:
        assert not mapgen.is_legal_move(m, node, n)


def test_illegal_move_is_rejected():
    m = mapgen.generate(7, 1)
    start = m.row_nodes(0)[0]
    reachable = {n.key for n in m.next_nodes(start)}
    off_path = [n for n in m.row_nodes(1) if n.key not in reachable]
    assert off_path, "seed 7 row 1 should have a node off the entry's edges"
    for n in off_path:
        assert not mapgen.is_legal_move(m, start, n)
    assert mapgen.is_legal_move(m, start, m.next_nodes(start)[0])
    assert not mapgen.is_legal_move(m, start, start)


def test_a_full_climb_reaches_the_preboss_row():
    m = mapgen.generate(21, 3)
    node = mapgen.legal_moves(m, None)[0]
    visited = [node]
    while node.row < m.rows - 1:
        node = mapgen.legal_moves(m, node)[0]
        visited.append(node)
    assert len(visited) == m.rows
    assert node.kind == "rest"


# --------------------------------------------------------------------------
# per-floor rng isolation
# --------------------------------------------------------------------------


def test_floor_rng_is_isolated():
    a = mapgen.floor_rng(1234, 5).random()
    b = mapgen.floor_rng(1234, 5).random()
    c = mapgen.floor_rng(1234, 6).random()
    assert a == b
    assert a != c


# --------------------------------------------------------------------------
# the lever
# --------------------------------------------------------------------------


def test_check_invariants_passes_for_generated_maps():
    for m in all_maps():
        assert mapgen.check_invariants(m) == []


def test_known_hard_seeds_generate_legal_maps():
    """Regression pins.

    These two produced an illegal graph: a node with three children on a row
    whose next row had only two columns, so no edit on the children's row could
    separate them. The repair pass now unsplits the parent, and generate()
    re-walks and raises rather than returning an illegal map.
    """
    for seed, act in KNOWN_HARD:
        m = mapgen.generate(seed, act)
        assert mapgen.check_invariants(m) == [], f"seed {seed} act {act}"


def test_generate_never_returns_an_illegal_map_over_a_wide_sweep():
    for seed in range(400, 700):
        for act in (4, 5, 6):
            m = mapgen.generate(seed, act)
            assert mapgen.check_invariants(m) == [], f"seed {seed} act {act}"


def test_check_invariants_catches_a_broken_map():
    m = mapgen.generate(3, 1)
    victim = m.row_nodes(1)[0]
    m.nodes[victim.key] = victim.replace(kind="rest")
    assert mapgen.check_invariants(m)


def test_verify_cli_reports_clean(capsys):
    assert mapgen.main(["verify", "--seeds", "5"]) == 0
    assert "ok" in capsys.readouterr().out.lower()


def test_show_cli_emits_json(capsys):
    assert mapgen.main(["show", "--seed", "8", "--act", "1", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["rows"] == 15
    assert data["nodes"]
