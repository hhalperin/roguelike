"""Tests for record_play.py — the self-contained script dealt into target repos."""
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "record_play.py"


def _run(path, name, session_id=None):
    payload = json.dumps({"session_id": session_id}) if session_id else ""
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--path", str(path), "--name", name],
        input=payload, capture_output=True, text=True, check=False,
    )


def test_credits_existing_card(tmp_path):
    d = tmp_path / ".claude"
    d.mkdir()
    (d / "deck.json").write_text(json.dumps({
        "cards": [{"name": "run-tests", "plays": 0, "last_played": None}],
    }))
    result = _run(tmp_path, "run-tests")
    assert result.returncode == 0
    data = json.loads((d / "deck.json").read_text())
    assert data["cards"][0]["plays"] == 1
    assert data["cards"][0]["last_played"]


def test_noop_for_unknown_card(tmp_path):
    d = tmp_path / ".claude"
    d.mkdir()
    (d / "deck.json").write_text(json.dumps({"cards": []}))
    result = _run(tmp_path, "ghost")
    assert result.returncode == 0
    assert json.loads((d / "deck.json").read_text())["cards"] == []


def test_noop_without_deck(tmp_path):
    result = _run(tmp_path, "run-tests")
    assert result.returncode == 0


def test_second_stop_in_same_session_does_not_double_count(tmp_path):
    d = tmp_path / ".claude"
    d.mkdir()
    (d / "deck.json").write_text(json.dumps({
        "cards": [{"name": "run-tests", "plays": 0, "last_played": None}],
    }))
    _run(tmp_path, "run-tests", session_id="sess-1")
    result = _run(tmp_path, "run-tests", session_id="sess-1")
    assert result.returncode == 0
    data = json.loads((d / "deck.json").read_text())
    assert data["cards"][0]["plays"] == 1  # second Stop in the same session is a no-op


def test_new_session_credits_again(tmp_path):
    d = tmp_path / ".claude"
    d.mkdir()
    (d / "deck.json").write_text(json.dumps({
        "cards": [{"name": "run-tests", "plays": 0, "last_played": None}],
    }))
    _run(tmp_path, "run-tests", session_id="sess-1")
    _run(tmp_path, "run-tests", session_id="sess-2")
    data = json.loads((d / "deck.json").read_text())
    assert data["cards"][0]["plays"] == 2
