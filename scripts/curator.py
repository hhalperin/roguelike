#!/usr/bin/env python3
"""spire :: curator.py — the reward judge.

Called by ``reward_gate.py`` (never directly by a hook) once the deterministic
gate has already decided a session is worth judging. Uses the Python
``claude-agent-sdk`` to make one cheap-model, tool-free call that returns
strict, schema-validated JSON: offer up to three cards, or skip.

**This is the one place in the engine that is not pure stdlib** — CLAUDE.md's
"scripts are pure standard library" rule applies to the deterministic core
(``scan.py``, ``deck.py``); judgment inherently needs a model. The dependency
is optional and soft: if ``claude-agent-sdk`` isn't installed, or the call
fails for any reason, ``judge()`` returns a "skip" verdict rather than raising
— the reward loop is a bonus, never a point of failure for the session.

House rules (baked into the system prompt, in order):
    1. Default recommendation is skip.
    2. Offer only for a pattern that has repeated, or a mistake that has bitten
       more than once — never a one-off.
    3. Soft cap ~12 cards: past it, every offer must name a card to remove.
    4. Offer at most 3 cards per judgment.
"""
from __future__ import annotations

import json
from typing import Any

try:
    import anyio
    import claude_agent_sdk as sdk

    SDK_AVAILABLE = True
except ImportError:
    anyio = None  # explicit sentinels so the names always exist (and are safely
    sdk = None    # monkeypatchable in tests) even when the soft dependency is absent
    SDK_AVAILABLE = False

DEFAULT_MODEL = "claude-haiku-4-5"
TIMEOUT_SECONDS = 45
SOFT_CAP = 12

SKIP = {"recommend": "skip", "reason": "", "offer": [], "remove": []}

OFFER_SCHEMA = {
    "type": "object",
    "properties": {
        "recommend": {"type": "string", "enum": ["skip", "offer"]},
        "reason": {"type": "string"},
        "offer": {
            "type": "array",
            "maxItems": 3,
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"type": "string", "enum": ["skill", "relic", "power"]},
                    "description": {"type": "string"},
                    "rationale": {"type": "string"},
                },
                "required": ["name", "type", "description", "rationale"],
                "additionalProperties": False,
            },
        },
        "remove": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["recommend", "reason", "offer", "remove"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = f"""\
You are spire's curator: a terse, disciplined judge of whether a
coding session's work earns a new "card" (a Claude Code skill, relic, or
power) for this repository's deck.

House rules, in order, and they override any temptation to be generous:
1. Default to "skip". Most sessions earn nothing - a high skip rate is
   healthy, not a failure of judgment.
2. Only recommend "offer" for a pattern that has clearly REPEATED (the same
   kind of task done multiple times this session or across recent history)
   or a mistake that has bitten more than once. Never offer a card for a
   single one-off action, however impressive.
3. Soft cap: if the deck already has {SOFT_CAP} or more cards, any offer MUST
   name at least one existing card in "remove" - a trade, not pure growth.
4. Offer at most 3 cards. Keep names kebab-case and descriptions short (one
   sentence).
5. Prefer deterministic enforcement over a new card: if the repeated thing is
   already covered by an existing relic or card, skip.

You are given the current deck (class, existing cards/relics, reward
history) and a summary of what changed this session (git diff stat, a raw
activity-event count). Decide strictly from this evidence - do not invent
context you were not given, and do not ask questions; this is a one-shot,
non-interactive judgment.
"""


def _build_prompt(deck: dict, context: str) -> str:
    cards = ", ".join(c.get("name", "?") for c in deck.get("cards", [])) or "none"
    relics = ", ".join(deck.get("relics", [])) or "none"
    rewards = deck.get("rewards", {})
    return (
        f"Deck class: {deck.get('class', 'unknown')}\n"
        f"Existing cards ({len(deck.get('cards', []))}): {cards}\n"
        f"Existing relics: {relics}\n"
        f"Reward history: {rewards.get('offered', 0)} offered, "
        f"{rewards.get('taken', 0)} taken, {rewards.get('skipped', 0)} skipped\n\n"
        f"What changed this session:\n{context}\n\n"
        "Judge per the house rules and answer only via the provided schema."
    )


async def _judge_async(deck: dict, context: str, model: str, cwd: str | None) -> dict:
    options = sdk.ClaudeAgentOptions(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        allowed_tools=[],
        max_turns=1,
        cwd=cwd,
        output_format={"type": "json_schema", "schema": OFFER_SCHEMA},
    )
    final_text = None
    structured: dict | None = None
    is_error = False
    # Let the async-for loop finish naturally rather than returning from
    # inside it: an early return while sdk.query()'s generator is still open
    # races its cleanup against fail_after's cancel scope and can surface a
    # spurious (near-empty-message) exception on an otherwise-successful call.
    with anyio.fail_after(TIMEOUT_SECONDS):
        async for msg in sdk.query(prompt=_build_prompt(deck, context), options=options):
            if type(msg).__name__ == "ResultMessage":
                is_error = bool(getattr(msg, "is_error", False))
                raw_structured = getattr(msg, "structured_output", None)
                if raw_structured is not None:
                    structured = dict(raw_structured)
                else:
                    final_text = getattr(msg, "result", None)

    if structured is not None:
        return structured
    if is_error or not final_text:
        return dict(SKIP, reason="curator call reported an error or produced no output")
    return json.loads(final_text)


def judge(
    deck: dict, context: str, model: str = DEFAULT_MODEL, cwd: str | None = None
) -> dict[str, Any]:
    """Judge whether this session's work earns a reward offer.

    ``cwd`` should be the target repo's path - the underlying SDK spawns its
    own ``claude`` subprocess, which otherwise inherits whatever directory the
    calling hook process happens to be in.

    Always returns a dict matching OFFER_SCHEMA's shape. Never raises - any
    failure (missing dependency, timeout, API error, malformed output)
    degrades to a "skip" verdict with a human-readable reason.
    """
    if not SDK_AVAILABLE:
        return dict(SKIP, reason="claude-agent-sdk not installed; reward loop disabled")
    try:
        result = anyio.run(_judge_async, deck, context, model, cwd)
    except Exception as exc:  # noqa: BLE001 - deliberately broad: never break the caller
        return dict(SKIP, reason=f"curator error: {exc!r}")

    if not isinstance(result, dict) or result.get("recommend") not in ("skip", "offer"):
        return dict(SKIP, reason="curator returned a malformed verdict")
    result.setdefault("reason", "")
    result.setdefault("offer", [])
    result.setdefault("remove", [])
    return result


if __name__ == "__main__":
    # Manual smoke test: `python3 curator.py '<deck.json path>' '<context text>'`
    import sys

    _default_deck = {"class": "defect", "cards": [], "relics": []}
    deck_arg = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else _default_deck
    context_arg = sys.argv[2] if len(sys.argv) > 2 else "1 file changed, 40 insertions(+)"
    print(json.dumps(judge(deck_arg, context_arg), indent=2))
