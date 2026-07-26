"""Guard the generated demo map data against drift.

design/spire-ai/ui/demo/mapdata.js is produced by `mapgen.py emit-js`. Nothing
stops someone changing the generator and forgetting to regenerate it, which
would leave the demo rendering maps the engine no longer produces. This test
makes that fail instead of going unnoticed.
"""
import json
import pathlib

import mapgen

MAPDATA = (
    pathlib.Path(__file__).resolve().parent.parent
    / "design"
    / "spire-ai"
    / "ui"
    / "demo"
    / "mapdata.js"
)


def committed_payload():
    """Parse the two globals mapdata.js assigns.

    Deliberately strict. A format change should fail with a readable message
    rather than an IndexError from a bare split.
    """
    text = MAPDATA.read_text(encoding="utf-8")
    parts = {}
    for name in ("window.SPIRE_MAPS", "window.SPIRE_RAMP"):
        marker = name + " ="
        assert marker in text, f"{MAPDATA.name} no longer assigns {name}"
        parts[name] = text.split(marker, 1)[1]
    maps_body = parts["window.SPIRE_MAPS"].rsplit("window.SPIRE_RAMP", 1)[0]
    return (
        json.loads(maps_body.strip().rstrip(";")),
        json.loads(parts["window.SPIRE_RAMP"].strip().rstrip(";")),
    )


def committed_maps():
    return committed_payload()[0]


def test_mapdata_exists():
    assert MAPDATA.is_file(), f"missing {MAPDATA}"


def test_mapdata_matches_the_generator():
    expected = [
        mapgen.generate(seed, act).to_dict()
        for seed in range(mapgen.EMIT_SEEDS)
        for act in range(1, mapgen.EMIT_ACTS + 1)
    ]
    assert committed_maps() == expected, (
        "mapdata.js is stale. Regenerate it:\n"
        "  python3 scripts/mapgen.py emit-js > design/spire-ai/ui/demo/mapdata.js"
    )


def test_ramp_config_is_exported_not_duplicated():
    """The client must read the ramp from the engine, never hardcode it."""
    _, ramp = committed_payload()
    assert ramp["order"] == list(mapgen.RAMP_ORDER)
    assert ramp["base"] == dict(mapgen.RAMP_BASE)


def test_committed_nodes_match_the_generator_node_for_node():
    """Checks the shipped nodes, not a regenerated stand-in.

    An earlier version regenerated the map and validated that instead, which
    would have passed even if mapdata.js held completely different nodes.
    """
    for payload in committed_maps():
        spire_map = mapgen.generate(payload["seed"], payload["act"])
        assert mapgen.check_invariants(spire_map) == []
        assert payload["nodes"] == spire_map.to_dict()["nodes"], (
            f"committed nodes differ for seed {payload['seed']} act {payload['act']}"
        )
        assert payload["boss"] == spire_map.boss
