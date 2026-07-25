"""Validate the plugin's manifests and every SKILL.md frontmatter.

These are the structural checks `claude plugin validate` performs, expressed as
tests so CI can run them without the Claude Code CLI. Skips if PyYAML is absent.
"""
import json
import pathlib

import pytest

yaml = pytest.importorskip("yaml")

ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_plugin_manifest_valid():
    manifest = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    assert manifest["name"] == "spire"
    assert isinstance(manifest.get("version"), str)
    assert manifest.get("license") == "MIT"


def test_marketplace_manifest_valid():
    mp = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    assert mp["name"]
    plugins = mp["plugins"]
    assert len(plugins) == 1
    assert plugins[0]["name"] == "spire"
    assert plugins[0]["source"] == "./"


def _frontmatter(path):
    text = path.read_text()
    assert text.startswith("---"), f"{path}: missing frontmatter"
    return yaml.safe_load(text.split("---", 2)[1])


def test_every_skill_has_valid_frontmatter():
    skills = sorted((ROOT / "skills").glob("*/SKILL.md"))
    assert skills, "no skills found"
    for path in skills:
        meta = _frontmatter(path)
        assert isinstance(meta, dict), f"{path}: frontmatter is not a mapping"
        desc = meta.get("description")
        assert isinstance(desc, str) and desc.strip(), f"{path}: needs a description"
        for boolkey in ("disable-model-invocation", "user-invocable"):
            if boolkey in meta:
                assert isinstance(meta[boolkey], bool), f"{path}: {boolkey} must be boolean"


def test_command_skills_are_user_only():
    # Headline commands must not be model-invoked.
    for name in ("spire", "map", "shop"):
        meta = _frontmatter(ROOT / "skills" / name / "SKILL.md")
        assert meta.get("disable-model-invocation") is True, f"{name} must be user-invoked only"
