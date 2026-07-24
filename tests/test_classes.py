"""Schema + consistency checks for the class archetype YAML files.

Skipped automatically if PyYAML isn't installed, so the core scan/deck tests
never depend on a third-party package.
"""
import pathlib

import pytest

yaml = pytest.importorskip("yaml")

import deck  # noqa: E402  (import after importorskip)
import scan  # noqa: E402

CLASSES_DIR = pathlib.Path(__file__).resolve().parent.parent / "classes"
REQUIRED_TOP = {"class", "name", "detected_by", "flavor", "relics", "cards", "powers", "agent"}
EXPECTED = {"defect", "silent", "ironclad", "watcher", "colorless"}


def load_all():
    return {p: yaml.safe_load(p.read_text()) for p in sorted(CLASSES_DIR.glob("*.yaml"))}


def test_exactly_the_five_classes():
    assert {d["class"] for d in load_all().values()} == EXPECTED


def test_top_level_schema():
    for path, d in load_all().items():
        assert REQUIRED_TOP <= set(d), f"{path.name} missing {REQUIRED_TOP - set(d)}"
        assert d["class"] == path.stem, f"{path.name}: class != filename"


def test_relics_and_cards_well_formed():
    for path, d in load_all().items():
        assert d["relics"], f"{path.name}: needs at least one relic"
        for r in d["relics"]:
            assert {"id", "rule"} <= set(r), f"{path.name}: relic {r} missing id/rule"
        assert d["cards"], f"{path.name}: needs at least one card"
        for c in d["cards"]:
            assert {"name", "description", "body"} <= set(c), f"{path.name}: card missing keys"
            assert c["body"].strip(), f"{path.name}: card {c['name']} has empty body"


def test_classes_are_known_to_the_scripts():
    for d in load_all().values():
        assert d["class"] in deck.CLASS_NAMES, f"{d['class']} missing from deck.CLASS_NAMES"
        assert d["class"] in scan.FAMILY, f"{d['class']} missing from scan.FAMILY"
