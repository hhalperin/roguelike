"""Tests for ascend.py — the ascension ladder (A0-A20)."""
import json

import ascend
import deck
import pytest


@pytest.fixture(autouse=True)
def fixed_date(monkeypatch):
    monkeypatch.setenv("DECK_BUILDER_TODAY", "2026-07-24")


def _deal(tmp_path):
    deck.main(["init", "--path", str(tmp_path), "--class", "defect"])


def _settings(tmp_path):
    return json.loads((tmp_path / ".claude" / "settings.json").read_text())


def _write_settings(tmp_path, settings):
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir(exist_ok=True)
    (claude_dir / "settings.json").write_text(json.dumps(settings))


def _command_hook(command):
    return {"matcher": "*", "hooks": [{"type": "command", "command": command}]}


def test_show_without_deck_errors(tmp_path, capsys):
    assert ascend.main(["show", "--path", str(tmp_path)]) == 1


def test_show_renders_ladder(tmp_path, capsys):
    _deal(tmp_path)
    assert ascend.main(["show", "--path", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "A0" in out and "A20" in out
    assert "Current: A0" in out


def test_apply_rejects_invalid_tier(tmp_path):
    _deal(tmp_path)
    assert ascend.main(["apply", "--path", str(tmp_path), "--tier", "7"]) == 2


def test_apply_without_deck_writes_no_side_effects(tmp_path):
    # No deck.json at all - apply must fail before touching settings.json or
    # deck-builder-ascension.json, never leave a half-applied ascension.
    assert ascend.main(["apply", "--path", str(tmp_path), "--tier", "5",
                        "--lint-cmd", "ruff check ."]) == 1
    assert not (tmp_path / ".claude" / "settings.json").exists()
    assert not (tmp_path / ".claude" / "deck-builder-ascension.json").exists()


def test_apply_updates_deck_ascension(tmp_path):
    _deal(tmp_path)
    ascend.main(["apply", "--path", str(tmp_path), "--tier", "10",
                 "--lint-cmd", "ruff check .", "--test-cmd", "pytest"])
    assert deck.load(str(tmp_path))["ascension"] == 10


def test_apply_writes_ascension_config(tmp_path):
    _deal(tmp_path)
    ascend.main(["apply", "--path", str(tmp_path), "--tier", "10",
                 "--lint-cmd", "ruff check .", "--test-cmd", "pytest"])
    config = json.loads((tmp_path / ".claude" / "deck-builder-ascension.json").read_text())
    assert config == {
        "tier": 10, "lint_cmd": "ruff check .", "test_cmd": "pytest", "coverage_baseline": None,
    }


def test_apply_tier_5_adds_stop_hook(tmp_path):
    _deal(tmp_path)
    ascend.main(["apply", "--path", str(tmp_path), "--tier", "5", "--lint-cmd", "ruff check ."])
    stop = _settings(tmp_path)["hooks"]["Stop"]
    assert len(stop) == 1
    assert "ascension_gate.py" in stop[0]["hooks"][0]["command"]


def test_apply_tier_0_writes_no_stop_hook(tmp_path):
    _deal(tmp_path)
    ascend.main(["apply", "--path", str(tmp_path), "--tier", "0"])
    settings = _settings(tmp_path)
    assert "Stop" not in settings.get("hooks", {})


def test_apply_preserves_unrelated_settings(tmp_path):
    _deal(tmp_path)
    _write_settings(tmp_path, {
        "permissions": {"allow": ["Bash(git status)"]},
        "hooks": {"PostToolUse": [_command_hook("echo hi")]},
    })
    ascend.main(["apply", "--path", str(tmp_path), "--tier", "5", "--lint-cmd", "ruff check ."])
    settings = _settings(tmp_path)
    assert settings["permissions"]["allow"] == ["Bash(git status)"]
    assert settings["hooks"]["PostToolUse"][0]["hooks"][0]["command"] == "echo hi"
    assert len(settings["hooks"]["Stop"]) == 1


def test_apply_preserves_other_stop_hooks(tmp_path):
    _deal(tmp_path)
    _write_settings(tmp_path, {"hooks": {"Stop": [_command_hook("other-plugin.sh")]}})
    ascend.main(["apply", "--path", str(tmp_path), "--tier", "5", "--lint-cmd", "ruff check ."])
    stop = _settings(tmp_path)["hooks"]["Stop"]
    assert len(stop) == 2
    commands = [h["hooks"][0]["command"] for h in stop]
    assert "other-plugin.sh" in commands
    assert any("ascension_gate.py" in c for c in commands)


def test_reapply_replaces_not_duplicates(tmp_path):
    _deal(tmp_path)
    ascend.main(["apply", "--path", str(tmp_path), "--tier", "5", "--lint-cmd", "ruff check ."])
    ascend.main(["apply", "--path", str(tmp_path), "--tier", "20",
                 "--lint-cmd", "ruff check .", "--test-cmd", "pytest"])
    stop = _settings(tmp_path)["hooks"]["Stop"]
    assert len(stop) == 1


def test_deescalate_removes_our_entry_only(tmp_path):
    _deal(tmp_path)
    _write_settings(tmp_path, {"hooks": {"Stop": [_command_hook("other-plugin.sh")]}})
    ascend.main(["apply", "--path", str(tmp_path), "--tier", "10",
                 "--lint-cmd", "ruff check .", "--test-cmd", "pytest"])
    ascend.main(["apply", "--path", str(tmp_path), "--tier", "0"])
    stop = _settings(tmp_path)["hooks"]["Stop"]
    assert len(stop) == 1
    assert stop[0]["hooks"][0]["command"] == "other-plugin.sh"
    assert deck.load(str(tmp_path))["ascension"] == 0


def test_reapply_preserves_coverage_baseline(tmp_path):
    _deal(tmp_path)
    ascend.main(["apply", "--path", str(tmp_path), "--tier", "15",
                 "--lint-cmd", "ruff check .", "--test-cmd", "pytest"])
    config_path = tmp_path / ".claude" / "deck-builder-ascension.json"
    config = json.loads(config_path.read_text())
    config["coverage_baseline"] = 85.0
    config_path.write_text(json.dumps(config))

    # Re-applying (even at a different tier) must not reset the high-water
    # mark ascension_gate.py already established back to null.
    ascend.main(["apply", "--path", str(tmp_path), "--tier", "20",
                 "--lint-cmd", "ruff check .", "--test-cmd", "pytest"])
    assert json.loads(config_path.read_text())["coverage_baseline"] == 85.0
