"""Tests for paths.py — .spire layout + legacy .claude/ migration."""
import json

import deck
import engine_state
import paths


def test_new_deck_lives_under_spire(tmp_path):
    deck.main(["init", "--path", str(tmp_path), "--class", "defect"])
    assert (tmp_path / ".spire" / "deck.json").exists()
    assert not (tmp_path / ".claude" / "deck.json").exists()


def test_migrates_legacy_deck_and_ephemera(tmp_path):
    claude = tmp_path / ".claude"
    claude.mkdir()
    legacy_deck = {"schema_version": 1, "class": "defect", "classes": ["defect"]}
    (claude / "deck.json").write_text(json.dumps(legacy_deck))
    (claude / "deck-builder-state.json").write_text(json.dumps({
        "last_check_sha": "abc", "last_check_at": "t", "activity_count": 2,
    }))
    (claude / "deck-pending-reward.json").write_text(json.dumps({
        "reason": "x", "offer": [{"name": "card"}],
    }))
    (claude / "deck-builder-ascension.json").write_text(json.dumps({"tier": 5}))
    bin_dir = claude / "deck-builder"
    bin_dir.mkdir()
    (bin_dir / "record_play.py").write_text("# helper\n")

    paths.ensure_migrated(str(tmp_path))

    assert (tmp_path / ".spire" / "deck.json").exists()
    assert not (claude / "deck.json").exists()
    assert (tmp_path / ".spire" / "state.json").exists()
    assert (tmp_path / ".spire" / "pending-reward.json").exists()
    assert (tmp_path / ".spire" / "ascension.json").exists()
    assert (tmp_path / ".spire" / "bin" / "record_play.py").exists()
    assert engine_state.load_pending_reward(str(tmp_path))["offer"][0]["name"] == "card"


def test_migration_does_not_clobber_existing_spire(tmp_path):
    spire = tmp_path / ".spire"
    spire.mkdir()
    (spire / "deck.json").write_text(json.dumps({"class": "silent"}))
    claude = tmp_path / ".claude"
    claude.mkdir()
    (claude / "deck.json").write_text(json.dumps({"class": "defect"}))

    paths.ensure_migrated(str(tmp_path))

    assert json.loads((spire / "deck.json").read_text())["class"] == "silent"
    assert (claude / "deck.json").exists()  # left alone when dest exists


def test_rewrites_legacy_settings_gate_path(tmp_path):
    claude = tmp_path / ".claude"
    claude.mkdir()
    settings = {
        "hooks": {
            "Stop": [{
                "matcher": "*",
                "hooks": [{
                    "type": "command",
                    "command": (
                        'python3 "${CLAUDE_PROJECT_DIR}/.claude/deck-builder/ascension_gate.py"'
                    ),
                }],
            }],
        },
    }
    (claude / "settings.json").write_text(json.dumps(settings))
    (claude / "deck.json").write_text("{}")

    paths.ensure_migrated(str(tmp_path))

    updated = json.loads((claude / "settings.json").read_text())
    cmd = updated["hooks"]["Stop"][0]["hooks"][0]["command"]
    assert ".spire/bin/ascension_gate.py" in cmd
    assert ".claude/deck-builder/" not in cmd
