"""Schema checks for card packs (PyYAML; skips if absent)."""
import pathlib

import pytest

yaml = pytest.importorskip("yaml")

PACKS_DIR = pathlib.Path(__file__).resolve().parent.parent / "packs"
REQUIRED_TOP = {"pack", "name", "description", "relics", "cards"}


def load_all():
    return {
        p.parent.name: yaml.safe_load(p.read_text())
        for p in sorted(PACKS_DIR.glob("*/pack.yaml"))
    }


def test_at_least_one_pack():
    assert load_all(), "expected at least one pack under packs/"


def test_pack_schema():
    for name, data in load_all().items():
        assert REQUIRED_TOP <= set(data), f"{name}: missing {REQUIRED_TOP - set(data)}"
        assert data["pack"] == name, f"{name}: pack id must match directory"
        assert data["relics"] or data["cards"], f"{name}: empty pack"
        for r in data["relics"]:
            assert {"id", "rule"} <= set(r), f"{name}: relic missing id/rule"
        for c in data["cards"]:
            assert {"name", "description", "body"} <= set(c), f"{name}: card missing keys"
            assert c["body"].strip(), f"{name}: empty body for {c['name']}"
