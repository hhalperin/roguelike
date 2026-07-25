#!/usr/bin/env python3
"""spire :: engine_state.py — ephemeral engine bookkeeping.

Tracks activity between Stop-hook reward checks in
``<repo>/.spire/state.json``. This is deliberately **separate** from
``deck.json`` (the versioned save file): state here is disposable
bookkeeping the engine uses to decide when to bother judging a reward, not
part of the run a player would care about preserving. Pure stdlib.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths  # noqa: E402


def state_path(repo: str) -> str:
    paths.ensure_migrated(repo)
    return paths.state_path(repo)


def pending_reward_path(repo: str) -> str:
    paths.ensure_migrated(repo)
    return paths.pending_reward_path(repo)


def load_pending_reward(repo: str) -> dict | None:
    """The pending-reward payload, but ONLY if it's a genuine one: a dict
    with a non-empty ``offer``. A missing, corrupt, or offer-less file all
    return None identically - the single definition every caller (the Stop
    gate that must not pile onto an unresolved offer, and the SessionStart
    banner that surfaces it) shares, so they can never disagree on what
    counts as "pending" the way two separate re-implementations once did.
    """
    try:
        with open(pending_reward_path(repo), encoding="utf-8") as fh:
            data = json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict) or not data.get("offer"):
        return None
    return data


def load(repo: str) -> dict:
    path = state_path(repo)
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
            if isinstance(data, dict):
                return data
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return {"last_check_sha": None, "last_check_at": None, "activity_count": 0}


def save(repo: str, state: dict) -> None:
    path = state_path(repo)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2)
        fh.write("\n")
    os.replace(tmp, path)


def deck_exists(repo: str) -> bool:
    return paths.deck_exists(repo)
