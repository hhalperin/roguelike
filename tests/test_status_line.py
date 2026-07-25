"""Tests for status_line.py — the SessionStart hook."""
import json

import deck
import pytest
import status_line


@pytest.fixture(autouse=True)
def fixed_date(monkeypatch):
    monkeypatch.setenv("DECK_BUILDER_TODAY", "2026-07-24")


def test_no_deck_renders_nothing(tmp_path):
    assert status_line.render(str(tmp_path)) is None


def test_renders_class_and_counts(tmp_path):
    deck.main(["init", "--path", str(tmp_path), "--class", "defect"])
    deck.main(["add-card", "--path", str(tmp_path), "--name", "run-tests"])
    deck.main(["add-relic", "--path", str(tmp_path), "--id", "ruff-strict"])
    text = status_line.render(str(tmp_path))
    assert "The Defect" in text
    assert "1 cards" in text
    assert "1 relics" in text


def test_renders_pending_reward(tmp_path):
    deck.main(["init", "--path", str(tmp_path), "--class", "defect"])
    pending = tmp_path / ".claude" / "deck-pending-reward.json"
    pending.write_text(json.dumps({
        "reason": "repeated pattern",
        "offer": [{"name": "new-card", "type": "skill"}],
        "remove": [],
    }))
    text = status_line.render(str(tmp_path))
    assert "new-card" in text
    assert "campfire" in text


def test_malformed_deck_json_is_silent(tmp_path):
    d = tmp_path / ".claude"
    d.mkdir()
    (d / "deck.json").write_text("{not valid")
    assert status_line.render(str(tmp_path)) is None


def test_main_prints_nothing_without_deck(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    assert status_line.main() == 0
    assert capsys.readouterr().out == ""
