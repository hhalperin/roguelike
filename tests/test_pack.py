"""Tests for pack.py — list/locate community card packs."""
import json

import pack


def test_list_includes_testing_discipline():
    packs = pack.list_packs()
    names = {p["name"] for p in packs}
    assert "testing-discipline" in names
    assert all(p["path"].endswith("pack.yaml") for p in packs)


def test_path_resolves_known_pack():
    path = pack.pack_path("testing-discipline")
    assert path is not None
    assert path.endswith("testing-discipline/pack.yaml")


def test_path_rejects_unknown_and_unsafe(tmp_path):
    assert pack.pack_path("no-such-pack") is None
    assert pack.pack_path("../evil") is None
    assert pack.pack_path("..") is None


def test_list_cli_json(capsys):
    assert pack.main(["list", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert any(p["name"] == "testing-discipline" for p in data)


def test_path_cli(capsys):
    assert pack.main(["path", "testing-discipline"]) == 0
    assert "pack.yaml" in capsys.readouterr().out
    assert pack.main(["path", "missing"]) == 1
