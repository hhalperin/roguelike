"""Tests for record_play.py — the self-contained script dealt into target repos."""
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "record_play.py"


def _run(path, name):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--path", str(path), "--name", name],
        capture_output=True, text=True, check=False,
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
