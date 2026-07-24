"""Tests for reward_gate.py — the Stop-hook deterministic gate.

curator.judge is monkeypatched throughout: this file tests reward_gate's OWN
logic (candidate detection, state reset, pending-reward writing), not the
curator's judgment, which has its own dedicated tests.
"""
import json
import subprocess

import deck
import engine_state
import pytest
import reward_gate


@pytest.fixture(autouse=True)
def fixed_date(monkeypatch):
    monkeypatch.setenv("DECK_BUILDER_TODAY", "2026-07-24")


def _git_repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "README.md").write_text("hello\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=tmp_path, check=True)


def _deal(tmp_path):
    deck.main(["init", "--path", str(tmp_path), "--class", "defect"])


def _save_state(tmp_path, **kwargs):
    state = {"last_check_sha": None, "last_check_at": None, "activity_count": 0}
    state.update(kwargs)
    engine_state.save(str(tmp_path), state)


def test_noop_without_deck(tmp_path):
    reward_gate.run(str(tmp_path))  # must not raise even with no .claude/deck.json
    assert not (tmp_path / ".claude" / "deck-pending-reward.json").exists()


def test_below_threshold_does_nothing(tmp_path, monkeypatch):
    _deal(tmp_path)
    _save_state(tmp_path, last_check_sha="x", activity_count=1)
    called = []
    monkeypatch.setattr(reward_gate.curator, "judge", lambda *a, **k: called.append(1))
    reward_gate.run(str(tmp_path))
    assert called == []  # curator never invoked below the activity threshold


def test_candidate_by_activity_threshold_invokes_curator_and_resets_state(tmp_path, monkeypatch):
    _git_repo(tmp_path)
    _deal(tmp_path)
    _save_state(tmp_path, activity_count=reward_gate.ACTIVITY_THRESHOLD)
    skip_verdict = {"recommend": "skip", "reason": "nothing notable", "offer": [], "remove": []}
    monkeypatch.setattr(reward_gate.curator, "judge", lambda *a, **k: skip_verdict)

    reward_gate.run(str(tmp_path))

    state = engine_state.load(str(tmp_path))
    assert state["activity_count"] == 0
    assert state["last_check_sha"]  # populated from git HEAD
    assert not (tmp_path / ".claude" / "deck-pending-reward.json").exists()


def test_offer_verdict_writes_pending_reward_and_bumps_counter(tmp_path, monkeypatch):
    _git_repo(tmp_path)
    _deal(tmp_path)
    _save_state(tmp_path, activity_count=reward_gate.ACTIVITY_THRESHOLD)
    verdict = {
        "recommend": "offer", "reason": "repeated pattern",
        "offer": [{"name": "new-card", "type": "skill", "description": "d", "rationale": "r"}],
        "remove": [],
    }
    monkeypatch.setattr(reward_gate.curator, "judge", lambda *a, **k: verdict)

    reward_gate.run(str(tmp_path))

    pending = json.loads((tmp_path / ".claude" / "deck-pending-reward.json").read_text())
    assert pending["offer"][0]["name"] == "new-card"
    assert pending["reason"] == "repeated pattern"
    assert deck.load(str(tmp_path))["rewards"]["offered"] == 1


def test_new_commit_since_last_check_triggers_candidate_even_below_activity(tmp_path, monkeypatch):
    _git_repo(tmp_path)
    _deal(tmp_path)
    # Simulate a stale last_check_sha (a commit happened since), activity low.
    _save_state(tmp_path, last_check_sha="0" * 40, activity_count=0)
    invoked = []
    skip_verdict = {"recommend": "skip", "reason": "", "offer": [], "remove": []}

    def fake_judge(*a, **k):
        invoked.append(1)
        return skip_verdict

    monkeypatch.setattr(reward_gate.curator, "judge", fake_judge)
    reward_gate.run(str(tmp_path))
    assert invoked  # new commit alone is enough to trigger a candidate check


def test_main_never_raises_even_on_internal_error(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))

    def boom(repo):
        raise RuntimeError("boom")

    monkeypatch.setattr(reward_gate, "run", boom)
    assert reward_gate.main() == 0
