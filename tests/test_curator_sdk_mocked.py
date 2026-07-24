"""Tests for curator.py's SDK-integration path, with a fake claude-agent-sdk.

Needs real ``anyio`` (curator.py's async plumbing genuinely runs, only the
``sdk`` module itself is faked) so ``_judge_async``'s control flow — including
the fail_after/async-for interaction — is exercised for real. Skips itself if
anyio isn't installed, the same way tests/test_classes.py skips without
PyYAML: this is coverage CI doesn't require, but dev environments with the
optional dependency installed get the extra assurance.
"""
import json

import pytest

pytest.importorskip("anyio")

import curator  # noqa: E402


class ResultMessage:
    def __init__(self, structured_output=None, result=None, is_error=False):
        self.structured_output = structured_output
        self.result = result
        self.is_error = is_error


class _FakeOptions:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def _fake_sdk(final_message):
    async def fake_query(*, prompt, options):
        yield final_message

    return type(
        "FakeSDK", (), {"query": staticmethod(fake_query), "ClaudeAgentOptions": _FakeOptions}
    )


def test_judge_offer_path_with_mocked_sdk(monkeypatch):
    offer_msg = ResultMessage(structured_output={
        "recommend": "offer", "reason": "repeated 3x",
        "offer": [{"name": "x", "type": "skill", "description": "d", "rationale": "r"}],
        "remove": [],
    })
    monkeypatch.setattr(curator, "SDK_AVAILABLE", True)
    monkeypatch.setattr(curator, "sdk", _fake_sdk(offer_msg))
    verdict = curator.judge({"class": "defect", "cards": [], "relics": []}, "diff", cwd="/tmp")
    assert verdict["recommend"] == "offer"
    assert verdict["offer"][0]["name"] == "x"


def test_judge_result_text_fallback_json_parse(monkeypatch):
    text_msg = ResultMessage(result=json.dumps({
        "recommend": "skip", "reason": "one-off", "offer": [], "remove": [],
    }))
    monkeypatch.setattr(curator, "SDK_AVAILABLE", True)
    monkeypatch.setattr(curator, "sdk", _fake_sdk(text_msg))
    verdict = curator.judge({"class": "defect", "cards": [], "relics": []}, "diff")
    assert verdict["recommend"] == "skip"
    assert verdict["reason"] == "one-off"


def test_judge_is_error_becomes_skip(monkeypatch):
    err_msg = ResultMessage(is_error=True, result=None)
    monkeypatch.setattr(curator, "SDK_AVAILABLE", True)
    monkeypatch.setattr(curator, "sdk", _fake_sdk(err_msg))
    verdict = curator.judge({"class": "defect", "cards": [], "relics": []}, "diff")
    assert verdict["recommend"] == "skip"
