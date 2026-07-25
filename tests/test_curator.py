"""Tests for curator.py that need no optional dependency at all.

This is the path CI actually exercises: claude-agent-sdk (and its anyio
dependency) are an optional soft dependency of curator.py, never installed
for the enforced test suite. See test_curator_sdk_mocked.py for the
additional mocked-response tests that require anyio to be present.
"""
import curator


def test_skip_when_sdk_unavailable(monkeypatch):
    monkeypatch.setattr(curator, "SDK_AVAILABLE", False)
    verdict = curator.judge({"class": "defect", "cards": [], "relics": []}, "some diff")
    assert verdict["recommend"] == "skip"
    assert "not installed" in verdict["reason"]
    assert verdict["offer"] == []
    assert verdict["remove"] == []


def test_judge_never_raises_on_internal_exception(monkeypatch):
    monkeypatch.setattr(curator, "SDK_AVAILABLE", True)

    def boom(*args, **kwargs):
        raise RuntimeError("simulated SDK failure")

    monkeypatch.setattr(curator, "anyio", type("FakeAnyio", (), {"run": staticmethod(boom)}))
    verdict = curator.judge({"class": "defect", "cards": [], "relics": []}, "diff")
    assert verdict["recommend"] == "skip"
    assert "curator error" in verdict["reason"]


def test_judge_rejects_malformed_recommend(monkeypatch):
    monkeypatch.setattr(curator, "SDK_AVAILABLE", True)
    monkeypatch.setattr(
        curator, "anyio",
        type("FakeAnyio", (), {"run": staticmethod(lambda *a, **k: {"recommend": "maybe"})}),
    )
    verdict = curator.judge({"class": "defect", "cards": [], "relics": []}, "diff")
    assert verdict["recommend"] == "skip"
    assert "malformed" in verdict["reason"]


def test_judge_rejects_non_dict_result(monkeypatch):
    monkeypatch.setattr(curator, "SDK_AVAILABLE", True)
    monkeypatch.setattr(
        curator, "anyio",
        type("FakeAnyio", (), {"run": staticmethod(lambda *a, **k: "not a dict")}),
    )
    verdict = curator.judge({"class": "defect", "cards": [], "relics": []}, "diff")
    assert verdict["recommend"] == "skip"
