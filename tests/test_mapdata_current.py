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
    """Parse the two globals mapdata.js assigns."""
    out = {}
    for line in MAPDATA.read_text().splitlines():
        for name in ("window.SPIRE_MAPS", "window.SPIRE_RAMP"):
            if line.startswith(name):
                out[name] = line.split("=", 1)[1].strip().rstrip(";")
    # SPIRE_MAPS spans many lines; re-parse it from the whole file.
    text = MAPDATA.read_text()
    body = text.split("window.SPIRE_MAPS =", 1)[1]
    body = body.rsplit("window.SPIRE_RAMP", 1)[0].strip().rstrip(";")
    return json.loads(body), json.loads(out["window.SPIRE_RAMP"])


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


def test_committed_maps_are_legal():
    for payload in committed_maps():
        spire_map = mapgen.generate(payload["seed"], payload["act"])
        assert mapgen.check_invariants(spire_map) == []
