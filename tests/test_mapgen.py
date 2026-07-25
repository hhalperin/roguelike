"""Tests for mapgen.py.

These encode the Slay the Spire map-generation invariants documented in
design/spire-ai/sts-fidelity.md. They are property tests over many seeds
rather than fixtures, because the generator's contract is "every seed produces
a legal map", not "seed 7 produces this map".
"""
import itertools

import mapgen

SEEDS = list(range(40))
ACTS = (1, 2, 3)


def all_maps(ascension=0):
    for seed, act in itertools.product(SEEDS, ACTS):
        yield mapgen.generate(seed, act, ascension=ascension)


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
    assert len(shapes) == 3


# --------------------------------------------------------------------------
# shape and forced floors
# --------------------------------------------------------------------------


def test_dimensions():
    m = mapgen.generate(1, 1)
    assert m.rows == 15
    assert m.cols == 7
    assert all(0 <= n.col < 7 for n in m.nodes.values())
    assert all(0 <= n.row < 15 for n in m.nodes.values())


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
        for node in m.nodes.values():
            if node.row == m.rows - 1:
                assert node.next_cols == ()
            else:
                assert node.next_cols, f"dead end at {node.key}"


def test_edges_move_exactly_one_row_and_at_most_one_column():
    for m in all_maps():
        for node in m.nodes.values():
            for col in node.next_cols:
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
    """Monster is the fallback for an over-constrained node, so it may repeat."""
    assert "monster" not in mapgen.SIBLING_UNIQUE_KINDS
    assert "monster" not in mapgen.PARENT_UNIQUE_KINDS


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
    assert mapgen.legal_moves(m, None) == entries
    node = entries[0]
    moves = mapgen.legal_moves(m, node)
    assert moves == m.next_nodes(node)
    assert moves


def test_illegal_move_is_rejected():
    m = mapgen.generate(7, 1)
    start = m.row_nodes(0)[0]
    reachable = {n.key for n in m.next_nodes(start)}
    off_path = [
        n for n in m.row_nodes(1) if n.key not in reachable
    ]
    if off_path:
        assert not mapgen.is_legal_move(m, start, off_path[0])
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


def test_check_invariants_catches_a_broken_map():
    m = mapgen.generate(3, 1)
    victim = m.row_nodes(1)[0]
    m.nodes[victim.key] = victim.replace(kind="rest")
    assert mapgen.check_invariants(m)


def test_verify_cli_reports_clean(capsys):
    assert mapgen.main(["verify", "--seeds", "5"]) == 0
    assert "ok" in capsys.readouterr().out.lower()


def test_show_cli_emits_json(capsys):
    import json

    assert mapgen.main(["show", "--seed", "8", "--act", "1", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["rows"] == 15
    assert data["nodes"]
