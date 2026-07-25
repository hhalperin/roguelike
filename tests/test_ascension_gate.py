"""Tests for ascension_gate.py — the self-contained Stop-hook gate.

Run via subprocess (like test_record_play.py): this script is dealt into
target repos and must work standalone, so it's tested the way it's actually
invoked, not imported.
"""
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "ascension_gate.py"


def _run(tmp_path, config=None):
    if config is not None:
        spire_dir = tmp_path / ".spire"
        spire_dir.mkdir(exist_ok=True)
        (spire_dir / "ascension.json").write_text(json.dumps(config))
    env = {"CLAUDE_PROJECT_DIR": str(tmp_path), "PATH": "/usr/bin:/bin:/usr/local/bin"}
    return subprocess.run(
        [sys.executable, str(SCRIPT)], cwd=tmp_path, env=env,
        capture_output=True, text=True, check=False,
    )


def _config_after(tmp_path):
    return json.loads((tmp_path / ".spire" / "ascension.json").read_text())


def _cfg(tier, lint_cmd=None, test_cmd=None, coverage_baseline=None):
    return {
        "tier": tier, "lint_cmd": lint_cmd, "test_cmd": test_cmd,
        "coverage_baseline": coverage_baseline,
    }


def test_no_config_is_silent_noop(tmp_path):
    result = _run(tmp_path, config=None)
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_tier_below_5_never_runs_commands(tmp_path):
    result = _run(tmp_path, _cfg(0, lint_cmd="exit 1", test_cmd="exit 1"))
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_tier_5_blocks_on_lint_failure(tmp_path):
    result = _run(tmp_path, _cfg(5, lint_cmd="echo bad && exit 1"))
    decision = json.loads(result.stdout)
    assert decision["decision"] == "block"
    assert "lint" in decision["reason"].lower()


def test_tier_5_silent_on_lint_success(tmp_path):
    result = _run(tmp_path, _cfg(5, lint_cmd="exit 0"))
    assert result.stdout.strip() == ""


def test_tier_10_blocks_on_test_failure(tmp_path):
    result = _run(tmp_path, _cfg(10, lint_cmd="exit 0", test_cmd="echo failed && exit 1"))
    decision = json.loads(result.stdout)
    assert decision["decision"] == "block"
    assert "test" in decision["reason"].lower()


def test_tier_10_missing_test_cmd_does_not_block(tmp_path):
    result = _run(tmp_path, _cfg(10, lint_cmd="exit 0"))
    assert result.stdout.strip() == ""


def test_tier_15_sets_baseline_on_first_run(tmp_path):
    cfg = _cfg(15, lint_cmd="exit 0", test_cmd="echo 'TOTAL 100 85%' && exit 0")
    _run(tmp_path, cfg)
    assert _config_after(tmp_path)["coverage_baseline"] == 85.0


def test_tier_15_blocks_on_regression(tmp_path):
    cfg = _cfg(
        15, lint_cmd="exit 0", test_cmd="echo 'TOTAL 100 80%' && exit 0", coverage_baseline=90.0
    )
    result = _run(tmp_path, cfg)
    decision = json.loads(result.stdout)
    assert decision["decision"] == "block"
    assert "coverage" in decision["reason"].lower()


def test_tier_15_no_block_within_tolerance(tmp_path):
    cfg = _cfg(
        15, lint_cmd="exit 0", test_cmd="echo 'TOTAL 100 89.5%' && exit 0", coverage_baseline=90.0
    )
    result = _run(tmp_path, cfg)
    assert result.stdout.strip() == ""


def test_tier_15_no_coverage_found_is_silent(tmp_path):
    cfg = _cfg(
        15, lint_cmd="exit 0", test_cmd="echo 'all good' && exit 0", coverage_baseline=90.0
    )
    result = _run(tmp_path, cfg)
    assert result.stdout.strip() == ""


def test_malformed_config_fails_open(tmp_path):
    spire_dir = tmp_path / ".spire"
    spire_dir.mkdir(exist_ok=True)
    (spire_dir / "ascension.json").write_text("{not valid json")
    result = _run(tmp_path, config=None)
    assert result.returncode == 0
    assert result.stdout.strip() == ""
