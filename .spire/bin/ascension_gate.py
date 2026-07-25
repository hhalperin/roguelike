#!/usr/bin/env python3
"""ascension_gate.py — the Stop-hook gate for an ascended spire run.

**This file is dealt INTO target repos** at ``.spire/bin/ascension_gate.py``
by ``/spire:ascend``, and wired as a Stop hook in the target repo's own
``.claude/settings.json``. Like ``record_play.py``, it is deliberately
self-contained (no engine imports): config it reads was written once at
ascend-time, and it must keep enforcing that tier even if the spire plugin
is later uninstalled.

Reads ``.spire/ascension.json`` (tier + lint/test commands, written by
``ascend.py``; falls back to the legacy ``.claude/deck-builder-ascension.json``
path) and enforces progressively more of the ladder:

    A0  - no gate at all (this script isn't wired in until A5+)
    A5  - block the Stop if the lint command fails
    A10 - A5, plus block if the test command fails
    A15 - A10, plus block on a coverage regression (best-effort: only if a
          coverage percentage can be parsed from the test command's own
          output; otherwise this specific check silently no-ops rather than
          blocking on data we don't actually have)
    A20 - A15. (The "curator review required per room" half of A20 lives in
          reward_gate.py, which stops sampling and reviews every room once
          ascension reaches 20 - that's a judgment call, not a pass/fail gate,
          so it doesn't belong in this deterministic script.)

Never blocks for reasons outside its control: a missing/unset command for a
tier's check is a silent no-op for that check, never a block. Any unexpected
internal error also fails open (prints nothing, exits 0) - an ascension gate
that crashes and blocks every Stop indefinitely would be worse than one that
occasionally misses a real problem.
"""
from __future__ import annotations

import json
import os
import re
import subprocess

COVERAGE_TOLERANCE = 1.0  # percentage points of regression allowed before blocking
COVERAGE_RE = re.compile(r"(?:TOTAL|Total|Coverage)[^\n%]{0,40}?(\d{1,3}(?:\.\d+)?)\s*%")


def _config_path(repo: str) -> str:
    spire = os.path.join(repo, ".spire", "ascension.json")
    if os.path.exists(spire):
        return spire
    legacy = os.path.join(repo, ".claude", "deck-builder-ascension.json")
    if os.path.exists(legacy):
        return legacy
    return spire


def _load_config(repo: str) -> dict | None:
    try:
        with open(_config_path(repo), encoding="utf-8") as fh:
            data = json.load(fh)
            return data if isinstance(data, dict) else None
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _save_config(repo: str, config: dict) -> None:
    path = _config_path(repo)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(config, fh, indent=2)
        fh.write("\n")
    os.replace(tmp, path)


def _run(repo: str, command: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        command, shell=True, cwd=repo, capture_output=True, text=True, timeout=300, check=False,
    )


def _block(reason: str) -> int:
    print(json.dumps({"decision": "block", "reason": reason}))
    return 0  # exit 0: the JSON decision itself carries the "block", not the exit code


def _extract_coverage(output: str) -> float | None:
    match = COVERAGE_RE.search(output)
    return float(match.group(1)) if match else None


def check(repo: str, config: dict) -> int:
    tier = int(config.get("tier", 0))
    lint_cmd = config.get("lint_cmd")
    test_cmd = config.get("test_cmd")

    if tier >= 5 and lint_cmd:
        result = _run(repo, lint_cmd)
        if result.returncode != 0:
            tail = (result.stdout + result.stderr).strip()[-1500:]
            return _block(f"Ascension A{tier}: lint command failed.\n\n{tail}")

    test_output = ""
    if tier >= 10 and test_cmd:
        result = _run(repo, test_cmd)
        test_output = result.stdout + result.stderr
        if result.returncode != 0:
            tail = test_output.strip()[-1500:]
            return _block(f"Ascension A{tier}: test command failed.\n\n{tail}")

    if tier >= 15 and test_cmd and test_output:
        coverage = _extract_coverage(test_output)
        if coverage is not None:
            baseline = config.get("coverage_baseline")
            if isinstance(baseline, (int, float)) and coverage < baseline - COVERAGE_TOLERANCE:
                return _block(
                    f"Ascension A{tier}: coverage regressed from "
                    f"{baseline:.1f}% to {coverage:.1f}%."
                )
            if not isinstance(baseline, (int, float)) or coverage > baseline:
                config["coverage_baseline"] = coverage
                _save_config(repo, config)

    return 0


def main() -> int:
    repo = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    try:
        config = _load_config(repo)
        if not config:
            return 0
        return check(repo, config)
    except Exception:
        return 0  # fail open: never block a session over the gate's own bug


if __name__ == "__main__":
    raise SystemExit(main())
