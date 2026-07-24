"""Tests for scan.py — the deterministic stack detector."""
import scan


def write(root, rel, content="x"):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


def test_defect_python(tmp_path):
    write(tmp_path, "pyproject.toml", "[project]\nname='x'\n")
    for i in range(4):
        write(tmp_path, f"pkg/mod{i}.py", "x = 1\n")
    result = scan.scan(str(tmp_path))
    assert result["primary"] == "defect"
    assert "defect" in result["classes"]
    assert result["monorepo"] is False
    assert result["families"] == ["python"]


def test_silent_typescript(tmp_path):
    write(tmp_path, "package.json", '{"name":"x"}')
    write(tmp_path, "tsconfig.json", "{}")
    for i in range(3):
        write(tmp_path, f"src/c{i}.ts", "export const x = 1\n")
    result = scan.scan(str(tmp_path))
    assert result["primary"] == "silent"
    assert result["families"] == ["javascript"]
    assert result["monorepo"] is False


def test_ironclad_infra(tmp_path):
    write(tmp_path, "Dockerfile", "FROM python:3.12\n")
    write(tmp_path, "infra/main.tf", 'resource "null_resource" "x" {}\n')
    result = scan.scan(str(tmp_path))
    assert result["primary"] == "ironclad"
    assert "ironclad" in result["classes"]
    assert result["families"] == ["infra"]


def test_watcher_ml(tmp_path):
    # requirements.txt is also a Defect marker, but the ML signals must dominate.
    write(tmp_path, "requirements.txt", "torch==2.2.0\nnumpy\npandas\n")
    write(tmp_path, "analysis.ipynb", "{}")
    result = scan.scan(str(tmp_path))
    assert result["primary"] == "watcher"
    assert "watcher" in result["classes"]
    # Python-family only (defect + watcher) is NOT a monorepo.
    assert result["monorepo"] is False
    assert result["families"] == ["python"]


def test_colorless_default(tmp_path):
    write(tmp_path, "README.md", "# hello\n")
    write(tmp_path, "notes.txt", "nothing here\n")
    result = scan.scan(str(tmp_path))
    assert result["primary"] == "colorless"
    assert result["classes"] == ["colorless"]
    assert result["families"] == []
    assert result["monorepo"] is False


def test_monorepo_multi_family(tmp_path):
    write(tmp_path, "pyproject.toml", "[project]\nname='x'\n")
    write(tmp_path, "web/package.json", '{"name":"web"}')
    write(tmp_path, "deploy/Dockerfile", "FROM alpine\n")
    result = scan.scan(str(tmp_path))
    assert result["monorepo"] is True
    assert {"defect", "silent", "ironclad"} <= set(result["classes"])
    assert set(result["families"]) == {"python", "javascript", "infra"}


def test_ignored_dirs_are_pruned(tmp_path):
    # A package.json buried in node_modules must NOT make the repo a Silent.
    write(tmp_path, "node_modules/dep/package.json", '{"name":"dep"}')
    write(tmp_path, "README.md", "# hi\n")
    result = scan.scan(str(tmp_path))
    assert result["primary"] == "colorless"
    assert "silent" not in result["classes"]


def test_signals_are_reported(tmp_path):
    write(tmp_path, "pyproject.toml", "[project]\n")
    result = scan.scan(str(tmp_path))
    assert "pyproject.toml" in result["signals"]["defect"]
