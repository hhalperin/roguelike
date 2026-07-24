"""Tests for deck.py — the deck.json save-file manager."""
import json

import deck
import pytest


@pytest.fixture(autouse=True)
def fixed_date(monkeypatch):
    monkeypatch.setenv("DECK_BUILDER_TODAY", "2026-07-24")


def read_deck(root):
    return json.loads((root / ".claude" / "deck.json").read_text())


def test_init_creates_valid_deck(tmp_path):
    assert deck.main(["init", "--path", str(tmp_path), "--class", "defect"]) == 0
    data = read_deck(tmp_path)
    assert data["class"] == "defect"
    assert data["classes"] == ["defect"]
    assert data["act"] == 1 and data["floor"] == 0 and data["ascension"] == 0
    assert data["created"] == "2026-07-24"
    assert deck.validate(data) == []


def test_init_is_idempotent_without_force(tmp_path):
    assert deck.main(["init", "--path", str(tmp_path), "--class", "defect"]) == 0
    # A second init must refuse (non-zero) and leave the deck untouched.
    assert deck.main(["init", "--path", str(tmp_path), "--class", "silent"]) == 1
    assert read_deck(tmp_path)["class"] == "defect"


def test_init_force_overwrites(tmp_path):
    deck.main(["init", "--path", str(tmp_path), "--class", "defect"])
    assert deck.main(["init", "--path", str(tmp_path), "--class", "silent", "--force"]) == 0
    assert read_deck(tmp_path)["class"] == "silent"


def test_init_dual_class(tmp_path):
    deck.main(["init", "--path", str(tmp_path), "--class", "defect", "--class", "silent"])
    data = read_deck(tmp_path)
    assert data["class"] == "defect"
    assert data["classes"] == ["defect", "silent"]


def test_init_rejects_unknown_class(tmp_path):
    assert deck.main(["init", "--path", str(tmp_path), "--class", "wizard"]) == 2
    assert not (tmp_path / ".claude" / "deck.json").exists()


def test_add_card_and_dedup(tmp_path):
    deck.main(["init", "--path", str(tmp_path), "--class", "defect"])
    deck.main(["add-card", "--path", str(tmp_path), "--name", "add-endpoint", "--floor", "3"])
    deck.main(["add-card", "--path", str(tmp_path), "--name", "add-endpoint", "--floor", "5"])
    cards = read_deck(tmp_path)["cards"]
    assert len(cards) == 1
    assert cards[0]["name"] == "add-endpoint"
    assert cards[0]["added_floor"] == 3
    assert cards[0]["plays"] == 0 and cards[0]["last_played"] is None


def test_add_relic_and_dedup(tmp_path):
    deck.main(["init", "--path", str(tmp_path), "--class", "defect"])
    deck.main(["add-relic", "--path", str(tmp_path), "--id", "ruff-strict"])
    deck.main(["add-relic", "--path", str(tmp_path), "--id", "ruff-strict"])
    assert read_deck(tmp_path)["relics"] == ["ruff-strict"]


def test_add_power(tmp_path):
    deck.main(["init", "--path", str(tmp_path), "--class", "defect"])
    deck.main(["add-power", "--path", str(tmp_path), "--event", "PostToolUse",
               "--name", "auto-format"])
    powers = read_deck(tmp_path)["powers"]
    assert powers == [{"event": "PostToolUse", "name": "auto-format"}]


def test_show_renders(tmp_path, capsys):
    deck.main(["init", "--path", str(tmp_path), "--class", "defect"])
    deck.main(["add-card", "--path", str(tmp_path), "--name", "run-tests"])
    assert deck.main(["show", "--path", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "The Defect" in out
    assert "run-tests" in out


def test_show_without_deck_errors(tmp_path):
    assert deck.main(["show", "--path", str(tmp_path)]) == 1


def test_validate_good_deck(tmp_path):
    deck.main(["init", "--path", str(tmp_path), "--class", "defect"])
    assert deck.main(["validate", "--path", str(tmp_path)]) == 0


def test_validate_detects_malformed(tmp_path):
    bad = deck.skeleton(["defect"])
    del bad["act"]                       # missing required int
    bad["cards"] = [{"type": "skill"}]   # card missing name/added_floor/plays
    bad["rewards"] = {"offered": 0}      # missing taken/skipped
    errors = deck.validate(bad)
    assert any("act" in e for e in errors)
    assert any("cards[0]" in e for e in errors)
    assert any("rewards" in e for e in errors)


def test_validate_cli_on_malformed_json(tmp_path):
    d = tmp_path / ".claude"
    d.mkdir()
    (d / "deck.json").write_text("{not valid json")
    assert deck.main(["validate", "--path", str(tmp_path)]) == 1


def test_atomic_write_leaves_no_tmp(tmp_path):
    deck.main(["init", "--path", str(tmp_path), "--class", "defect"])
    deck.main(["add-card", "--path", str(tmp_path), "--name", "x"])
    claude_dir = tmp_path / ".claude"
    assert (claude_dir / "deck.json").exists()
    assert not (claude_dir / "deck.json.tmp").exists()


def test_bool_not_accepted_as_int(tmp_path):
    bad = deck.skeleton(["defect"])
    bad["floor"] = True   # bool must be rejected for an int field
    errors = deck.validate(bad)
    assert any("floor" in e for e in errors)
