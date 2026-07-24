"""Tests for activity_log.py — the PostToolUse hook."""
import json

import activity_log
import engine_state


def test_noop_without_deck(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    assert activity_log.main() == 0
    assert not (tmp_path / ".claude").exists()


def _deal(tmp_path):
    d = tmp_path / ".claude"
    d.mkdir()
    (d / "deck.json").write_text(json.dumps({"class": "defect", "cards": []}))


def test_increments_with_deck(tmp_path, monkeypatch):
    _deal(tmp_path)
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    activity_log.main()
    activity_log.main()
    assert engine_state.load(str(tmp_path))["activity_count"] == 2


def test_caps_growth(tmp_path, monkeypatch):
    _deal(tmp_path)
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    engine_state.save(
        str(tmp_path), {"last_check_sha": None, "last_check_at": None, "activity_count": 999}
    )
    activity_log.main()
    assert engine_state.load(str(tmp_path))["activity_count"] == 999
