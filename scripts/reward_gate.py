#!/usr/bin/env python3
"""deck-builder :: reward_gate.py — Stop hook: did a room clear?

The fast, deterministic half of the reward loop. Runs on every Stop event but
does almost nothing most of the time: only when there's a real deterministic
signal that something got done (a new commit, or enough tool-call activity
since the last check) does it bother invoking the curator. This keeps the
common case cheap and keeps the curator's judgment reserved for moments with
actual evidence to judge.

This hook must NEVER block or interrupt the session: reward offers are
detected here but only *surfaced* at the next SessionStart
(``status_line.py``) or via ``/deck-builder:campfire`` - never at Stop time.
Any failure anywhere in this script degrades to a silent no-op.
"""
from __future__ import annotations

import datetime
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import curator  # noqa: E402
import deck  # noqa: E402
import engine_state  # noqa: E402

ACTIVITY_THRESHOLD = 5  # tool calls since last check, absent a new commit


def _git(repo: str, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", repo, *args],
            capture_output=True, text=True, timeout=10, check=False,
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None


DIFF_CONTENT_LIMIT = 4000  # chars; enough to observe a repeated pattern, bounded for cost


def _diff_summary(repo: str, since_sha: str | None) -> str:
    """Stat summary + a bounded real diff, so the curator can see WHAT changed,
    not just how much - detecting "the same kind of thing done 3 times in this
    diff" needs actual content, not just a file/line count.
    """
    if since_sha:
        stat = _git(repo, "diff", "--stat", since_sha, "HEAD")
        content = _git(repo, "diff", since_sha, "HEAD")
    else:
        # No usable baseline (first check, or the sha is gone) - fall back to
        # whatever is currently uncommitted plus the last commit's message.
        stat = _git(repo, "diff", "--stat", "HEAD")
        content = _git(repo, "diff", "HEAD")
        last_commit = _git(repo, "log", "-1", "--pretty=%s")
        if last_commit:
            stat = f"{stat}\nlast commit: {last_commit}" if stat else f"last commit: {last_commit}"

    parts = []
    if stat:
        parts.append(f"--- diff --stat ---\n{stat}")
    if content:
        truncated = content[:DIFF_CONTENT_LIMIT]
        if len(content) > DIFF_CONTENT_LIMIT:
            truncated += "\n... (truncated)"
        parts.append(f"--- diff content ---\n{truncated}")
    return "\n\n".join(parts) or "no git diff available"


def _write_pending_reward(repo: str, verdict: dict) -> None:
    path = engine_state.pending_reward_path(repo)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = {
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "reason": verdict.get("reason", ""),
        "offer": verdict.get("offer", []),
        "remove": verdict.get("remove", []),
    }
    import json
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
        fh.write("\n")
    os.replace(tmp, path)


def run(repo: str) -> None:
    if not engine_state.deck_exists(repo):
        return
    if engine_state.load_pending_reward(repo) is not None:
        # An earlier offer is still awaiting a campfire decision - don't ask
        # the curator again (would silently replace it and double-count
        # rewards.offered). Resume normal gating once campfire resolves it.
        # Deliberately the SAME definition of "pending" status_line.py uses
        # (missing/corrupt/offer-less all count as "nothing pending"), so a
        # stale or malformed file can never deadlock the reward loop with no
        # visible hint - see engine_state.load_pending_reward.
        return

    the_deck = deck.load(repo)
    state = engine_state.load(repo)
    current_sha = _git(repo, "rev-parse", "HEAD")
    last_sha = state.get("last_check_sha")
    activity = int(state.get("activity_count", 0))

    # A20 ("full pipeline gate + curator review required per room") means the
    # curator samples every room instead of waiting for enough activity to
    # accumulate - so its threshold effectively drops to "anything happened."
    threshold = 1 if the_deck.get("ascension", 0) >= 20 else ACTIVITY_THRESHOLD

    new_commit = bool(current_sha and last_sha and current_sha != last_sha)
    # NOT `last_sha is None`: current_sha (and thus last_sha, once saved) is
    # also None whenever git has no HEAD, which would make every later check
    # look like a "first check" forever and bypass ACTIVITY_THRESHOLD. Only
    # last_check_at is guaranteed to be set once any check has ever run.
    first_check = state.get("last_check_at") is None
    candidate = new_commit or activity >= threshold or (first_check and activity > 0)
    if not candidate:
        return

    context = _diff_summary(repo, last_sha)
    verdict = curator.judge(the_deck, context, cwd=repo)

    # We've now considered this batch of work either way - reset the window.
    engine_state.save(repo, {
        "last_check_sha": current_sha,
        "last_check_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "activity_count": 0,
    })

    if verdict.get("recommend") == "offer" and verdict.get("offer"):
        _write_pending_reward(repo, verdict)
        deck.bump_reward(repo, "offered", len(verdict["offer"]))


def main() -> int:
    repo = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    try:
        run(repo)
    except Exception:
        # A reward offer is a bonus, never a reason to disrupt the session.
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
