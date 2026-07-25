"""Tests for deck.py — the deck.json save-file manager."""
import json

import deck
import pytest


@pytest.fixture(autouse=True)
def fixed_date(monkeypatch):
    monkeypatch.setenv("DECK_BUILDER_TODAY", "2026-07-24")


def read_deck(root):
    return json.loads((root / ".spire" / "deck.json").read_text())


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
    assert not (tmp_path / ".spire" / "deck.json").exists()


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
    d = tmp_path / ".spire"
    d.mkdir()
    (d / "deck.json").write_text("{not valid json")
    assert deck.main(["validate", "--path", str(tmp_path)]) == 1


def test_atomic_write_leaves_no_tmp(tmp_path):
    deck.main(["init", "--path", str(tmp_path), "--class", "defect"])
    deck.main(["add-card", "--path", str(tmp_path), "--name", "x"])
    spire_dir = tmp_path / ".spire"
    assert (spire_dir / "deck.json").exists()
    assert not (spire_dir / "deck.json.tmp").exists()


def test_bool_not_accepted_as_int(tmp_path):
    bad = deck.skeleton(["defect"])
    bad["floor"] = True   # bool must be rejected for an int field
    errors = deck.validate(bad)
    assert any("floor" in e for e in errors)


# --------------------------------------------------------------------------- #
# Act 2 mutators: rewards, removal, play-crediting
# --------------------------------------------------------------------------- #

def test_bump_reward(tmp_path):
    deck.main(["init", "--path", str(tmp_path), "--class", "defect"])
    assert deck.bump_reward(str(tmp_path), "offered", 2) == 2
    assert deck.bump_reward(str(tmp_path), "offered", 1) == 3
    assert read_deck(tmp_path)["rewards"]["offered"] == 3


def test_mark_offered_taken_skipped_cli(tmp_path):
    deck.main(["init", "--path", str(tmp_path), "--class", "defect"])
    deck.main(["mark-offered", "--path", str(tmp_path), "--count", "2"])
    deck.main(["mark-taken", "--path", str(tmp_path)])
    deck.main(["mark-skipped", "--path", str(tmp_path)])
    rewards = read_deck(tmp_path)["rewards"]
    assert rewards == {"offered": 2, "taken": 1, "skipped": 1}


def test_remove_card(tmp_path):
    deck.main(["init", "--path", str(tmp_path), "--class", "defect"])
    deck.main(["add-card", "--path", str(tmp_path), "--name", "run-tests"])
    skill_dir = tmp_path / ".claude" / "skills" / "run-tests"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# run-tests\n")

    assert deck.remove_card(str(tmp_path), "run-tests") is True

    assert read_deck(tmp_path)["cards"] == []
    assert not skill_dir.exists()  # dealt skill dir must go too, or it'd still load
    assert deck.remove_card(str(tmp_path), "run-tests") is False  # already gone


def test_remove_card_without_skill_dir_on_disk(tmp_path):
    """No .claude/skills/<name>/ present - must not error, just no-op the delete."""
    deck.main(["init", "--path", str(tmp_path), "--class", "defect"])
    deck.main(["add-card", "--path", str(tmp_path), "--name", "run-tests"])
    assert deck.remove_card(str(tmp_path), "run-tests") is True
    assert read_deck(tmp_path)["cards"] == []


def test_remove_card_rejects_path_traversal_name(tmp_path):
    # A card name isn't always human-typed (a curator offer can name one) -
    # a name with a path separator must never reach shutil.rmtree.
    deck.main(["init", "--path", str(tmp_path), "--class", "defect"])
    deck.main(["add-card", "--path", str(tmp_path), "--name", "../evil"])
    canary = tmp_path / ".claude" / "canary.txt"
    canary.parent.mkdir(parents=True, exist_ok=True)
    canary.write_text("must survive")

    assert deck.remove_card(str(tmp_path), "../evil") is True

    assert read_deck(tmp_path)["cards"] == []  # deck.json removal still proceeds
    assert canary.exists()  # rmtree must never have escaped .claude/skills/


def test_remove_card_rejects_bare_dotdot_name(tmp_path):
    deck.main(["init", "--path", str(tmp_path), "--class", "defect"])
    deck.main(["add-card", "--path", str(tmp_path), "--name", ".."])
    canary = tmp_path / ".claude" / "canary.txt"
    canary.parent.mkdir(parents=True, exist_ok=True)
    canary.write_text("must survive")

    assert deck.remove_card(str(tmp_path), "..") is True
    assert canary.exists()


def test_remove_relic(tmp_path):
    deck.main(["init", "--path", str(tmp_path), "--class", "defect"])
    deck.main(["add-relic", "--path", str(tmp_path), "--id", "ruff-strict"])
    assert deck.remove_relic(str(tmp_path), "ruff-strict") is True
    assert read_deck(tmp_path)["relics"] == []
    assert deck.remove_relic(str(tmp_path), "ruff-strict") is False


def test_remove_card_cli_exit_codes(tmp_path):
    deck.main(["init", "--path", str(tmp_path), "--class", "defect"])
    deck.main(["add-card", "--path", str(tmp_path), "--name", "run-tests"])
    assert deck.main(["remove-card", "--path", str(tmp_path), "--name", "run-tests"]) == 0
    assert deck.main(["remove-card", "--path", str(tmp_path), "--name", "run-tests"]) == 1


def test_record_play_function(tmp_path):
    deck.main(["init", "--path", str(tmp_path), "--class", "defect"])
    deck.main(["add-card", "--path", str(tmp_path), "--name", "run-tests"])
    assert deck.record_play(str(tmp_path), "run-tests") is True
    card = read_deck(tmp_path)["cards"][0]
    assert card["plays"] == 1
    assert card["last_played"] == "2026-07-24"
    assert deck.record_play(str(tmp_path), "ghost") is False


# --------------------------------------------------------------------------- #
# Act 3: deck stats
# --------------------------------------------------------------------------- #

def test_stats_summary_empty_deck(tmp_path):
    deck.main(["init", "--path", str(tmp_path), "--class", "defect"])
    s = deck.stats_summary(read_deck(tmp_path))
    assert s["card_count"] == 0
    assert s["total_plays"] == 0
    assert s["most_played"] is None
    assert s["unplayed"] == []
    assert s["reward_take_rate"] is None
    assert s["over_soft_cap"] is False


def test_stats_summary_mixed_deck(tmp_path):
    deck.main(["init", "--path", str(tmp_path), "--class", "defect"])
    deck.main(["add-card", "--path", str(tmp_path), "--name", "run-tests"])
    deck.main(["add-card", "--path", str(tmp_path), "--name", "add-endpoint"])
    deck.record_play(str(tmp_path), "run-tests")
    deck.record_play(str(tmp_path), "run-tests")
    deck.bump_reward(str(tmp_path), "offered", 3)
    deck.bump_reward(str(tmp_path), "taken", 1)

    s = deck.stats_summary(read_deck(tmp_path))
    assert s["card_count"] == 2
    assert s["total_plays"] == 2
    assert s["most_played"] == ("run-tests", 2)
    assert s["unplayed"] == ["add-endpoint"]
    assert s["reward_take_rate"] == pytest.approx(1 / 3)


def test_stats_summary_soft_cap(tmp_path):
    deck.main(["init", "--path", str(tmp_path), "--class", "defect"])
    for i in range(12):
        deck.main(["add-card", "--path", str(tmp_path), "--name", f"card-{i}"])
    assert deck.stats_summary(read_deck(tmp_path))["over_soft_cap"] is True


def test_stats_cli_without_deck_errors(tmp_path):
    assert deck.main(["stats", "--path", str(tmp_path)]) == 1


def test_stats_cli_renders(tmp_path, capsys):
    deck.main(["init", "--path", str(tmp_path), "--class", "defect"])
    deck.main(["add-card", "--path", str(tmp_path), "--name", "run-tests"])
    assert deck.main(["stats", "--path", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "Unplayed cards (1): run-tests" in out
    assert "no rewards offered yet" in out
