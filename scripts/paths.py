#!/usr/bin/env python3
"""spire :: paths.py — where the run lives vs where the agent loads primitives.

The run home is ``<repo>/.spire/`` (save file + disposable bookkeeping + dealt
helpers). Agent primitives stay where the agent looks for them
(``.claude/skills/``, ``CLAUDE.md``, ``.claude/settings.json``).

Also migrates pre-spire layouts that nested the save under ``.claude/``.
Pure stdlib; every engine script that touches the filesystem goes through here.
"""
from __future__ import annotations

import json
import os
import shutil

SPIRE_DIR = ".spire"
DECK_FILENAME = "deck.json"
STATE_FILENAME = "state.json"
PENDING_REWARD_FILENAME = "pending-reward.json"
ASCENSION_FILENAME = "ascension.json"
BIN_DIRNAME = "bin"

# Pre-spire locations (deck-builder nested the save under .claude/).
_LEGACY_DECK = (".claude", "deck.json")
_LEGACY_STATE = (".claude", "deck-builder-state.json")
_LEGACY_PENDING = (".claude", "deck-pending-reward.json")
_LEGACY_ASCENSION = (".claude", "deck-builder-ascension.json")
_LEGACY_BIN = (".claude", "deck-builder")

_LEGACY_GATE_SNIPPET = ".claude/deck-builder/ascension_gate.py"
_SPIRE_GATE_SNIPPET = ".spire/bin/ascension_gate.py"


def spire_dir(repo: str) -> str:
    return os.path.join(repo, SPIRE_DIR)


def deck_path(repo: str) -> str:
    return os.path.join(repo, SPIRE_DIR, DECK_FILENAME)


def state_path(repo: str) -> str:
    return os.path.join(repo, SPIRE_DIR, STATE_FILENAME)


def pending_reward_path(repo: str) -> str:
    return os.path.join(repo, SPIRE_DIR, PENDING_REWARD_FILENAME)


def ascension_path(repo: str) -> str:
    return os.path.join(repo, SPIRE_DIR, ASCENSION_FILENAME)


def bin_dir(repo: str) -> str:
    return os.path.join(repo, SPIRE_DIR, BIN_DIRNAME)


def record_play_path(repo: str) -> str:
    return os.path.join(bin_dir(repo), "record_play.py")


def ascension_gate_path(repo: str) -> str:
    return os.path.join(bin_dir(repo), "ascension_gate.py")


def skills_dir(repo: str) -> str:
    """Agent-facing cards — still under .claude so Claude Code loads them."""
    return os.path.join(repo, ".claude", "skills")


def settings_path(repo: str) -> str:
    """Agent settings (ascension Stop hook) — platform-owned, not run state."""
    return os.path.join(repo, ".claude", "settings.json")


def deck_exists(repo: str) -> bool:
    ensure_migrated(repo)
    return os.path.exists(deck_path(repo))


def _move_if_absent(src: str, dest: str) -> None:
    if not os.path.exists(src) or os.path.exists(dest):
        return
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.move(src, dest)


def _migrate_bin(repo: str) -> None:
    legacy = os.path.join(repo, *_LEGACY_BIN)
    dest = bin_dir(repo)
    if not os.path.isdir(legacy):
        return
    os.makedirs(dest, exist_ok=True)
    for name in ("record_play.py", "ascension_gate.py"):
        _move_if_absent(os.path.join(legacy, name), os.path.join(dest, name))
    try:
        if not os.listdir(legacy):
            os.rmdir(legacy)
    except OSError:
        pass


def _rewrite_settings_gate_path(repo: str) -> None:
    path = settings_path(repo)
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return
    if not isinstance(data, dict):
        return
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        return
    stop = hooks.get("Stop")
    if not isinstance(stop, list):
        return
    changed = False
    for entry in stop:
        if not isinstance(entry, dict):
            continue
        for hook in entry.get("hooks", []):
            if not isinstance(hook, dict):
                continue
            cmd = hook.get("command", "")
            if _LEGACY_GATE_SNIPPET in cmd:
                hook["command"] = cmd.replace(_LEGACY_GATE_SNIPPET, _SPIRE_GATE_SNIPPET)
                changed = True
    if not changed:
        return
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")
    os.replace(tmp, path)


def ensure_migrated(repo: str) -> None:
    """Move a pre-spire ``.claude/`` save layout into ``.spire/`` once.

    Idempotent. Prefer existing ``.spire/`` files over legacy ones when both
    exist (never clobber a newer run). Safe to call on every engine entrypoint.
    """
    _move_if_absent(os.path.join(repo, *_LEGACY_DECK), deck_path(repo))
    _move_if_absent(os.path.join(repo, *_LEGACY_STATE), state_path(repo))
    _move_if_absent(os.path.join(repo, *_LEGACY_PENDING), pending_reward_path(repo))
    _move_if_absent(os.path.join(repo, *_LEGACY_ASCENSION), ascension_path(repo))
    _migrate_bin(repo)
    _rewrite_settings_gate_path(repo)
