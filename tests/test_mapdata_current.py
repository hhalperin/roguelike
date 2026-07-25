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
EMIT_SEEDS = 4


def committed_maps():
    text = MAPDATA.read_text()
    payload = text.split("=", 1)[1].strip().rstrip(";")
    return json.loads(payload)


def test_mapdata_exists():
    assert MAPDATA.is_file(), f"missing {MAPDATA}"


def test_mapdata_matches_the_generator():
    expected = [
        mapgen.generate(seed, act).to_dict()
        for seed in range(EMIT_SEEDS)
        for act in sorted(mapgen.ACT_SEED_OFFSET)
    ]
    assert committed_maps() == expected, (
        "mapdata.js is stale. Regenerate it:\n"
        "  python3 scripts/mapgen.py emit-js > design/spire-ai/ui/demo/mapdata.js"
    )


def test_committed_maps_are_legal():
    for payload in committed_maps():
        spire_map = mapgen.generate(payload["seed"], payload["act"])
        assert mapgen.check_invariants(spire_map) == []
