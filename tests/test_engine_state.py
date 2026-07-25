"""Tests for engine_state.py — ephemeral Stop-hook bookkeeping."""
import json

import engine_state


def test_load_defaults_when_missing(tmp_path):
    state = engine_state.load(str(tmp_path))
    assert state == {"last_check_sha": None, "last_check_at": None, "activity_count": 0}


def test_save_load_round_trip(tmp_path):
    engine_state.save(
        str(tmp_path), {"last_check_sha": "abc", "last_check_at": "t", "activity_count": 3}
    )
    assert engine_state.load(str(tmp_path)) == {
        "last_check_sha": "abc", "last_check_at": "t", "activity_count": 3,
    }


def test_load_tolerates_malformed_json(tmp_path):
    d = tmp_path / ".claude"
    d.mkdir()
    (d / "deck-builder-state.json").write_text("{not json")
    state = engine_state.load(str(tmp_path))
    assert state["activity_count"] == 0


def test_deck_exists(tmp_path):
    assert engine_state.deck_exists(str(tmp_path)) is False
    d = tmp_path / ".claude"
    d.mkdir()
    (d / "deck.json").write_text("{}")
    assert engine_state.deck_exists(str(tmp_path)) is True


def test_load_pending_reward_missing(tmp_path):
    assert engine_state.load_pending_reward(str(tmp_path)) is None


def test_load_pending_reward_malformed_json(tmp_path):
    d = tmp_path / ".claude"
    d.mkdir()
    (d / "deck-pending-reward.json").write_text("{not json")
    assert engine_state.load_pending_reward(str(tmp_path)) is None


def test_load_pending_reward_without_offer_is_not_pending(tmp_path):
    d = tmp_path / ".claude"
    d.mkdir()
    (d / "deck-pending-reward.json").write_text(json.dumps({"reason": "x", "offer": []}))
    assert engine_state.load_pending_reward(str(tmp_path)) is None


def test_load_pending_reward_valid(tmp_path):
    d = tmp_path / ".claude"
    d.mkdir()
    (d / "deck-pending-reward.json").write_text(json.dumps({
        "reason": "repeated pattern", "offer": [{"name": "new-card"}],
    }))
    pending = engine_state.load_pending_reward(str(tmp_path))
    assert pending["offer"][0]["name"] == "new-card"
