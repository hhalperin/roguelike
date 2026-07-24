#!/usr/bin/env python3
"""deck-builder :: scan.py — deterministic repo stack detector.

Walks a target repository and detects its roguelike "class" (archetype) purely
from the files present. Standard library only: no third-party dependencies, no
network, no LLM. Emits a JSON summary on stdout that the ``/deck-builder`` skill
interprets to deal a starter deck.

Classes
-------
    defect     python / backend      (pyproject.toml, setup.py, requirements.txt)
    silent     typescript / frontend (package.json, tsconfig.json, *.ts)
    ironclad   infra / IaC           (Dockerfile, *.tf, terraform/, compose)
    watcher    data / ML             (*.ipynb, notebooks/, ML deps, models/)
    colorless  anything else         (minimal, safe default)

Multiple classes within one language family (e.g. defect + watcher for a Python
ML project) are reported together without being flagged a monorepo. A monorepo
is when strong signals span two or more *families* (python / javascript / infra).

Usage
-----
    python scan.py [PATH]        # PATH defaults to the current directory

Output is indented JSON, always parseable, e.g.::

    {
      "path": "/abs/path",
      "primary": "defect",
      "classes": ["defect"],
      "families": ["python"],
      "monorepo": false,
      "scores": {"defect": 4},
      "signals": {"defect": ["pyproject.toml", "requirements.txt"]}
    }
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

# Directories we never descend into — build output, caches, vendored deps, VCS.
IGNORE_DIRS = frozenset({
    ".git", ".hg", ".svn", "node_modules", ".venv", "venv", "env", "ENV",
    "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".tox",
    ".nox", ".terraform", "dist", "build", "target", ".next", ".nuxt",
    "site-packages", "coverage", "htmlcov", ".idea", ".vscode", "vendor",
    ".gradle", ".cache", "bower_components",
})

# ML/data-science libraries whose presence in a dependency file marks a Watcher.
ML_LIBS = (
    "numpy", "pandas", "scipy", "matplotlib", "seaborn", "scikit-learn",
    "sklearn", "torch", "pytorch", "torchvision", "tensorflow", "keras",
    "jax", "flax", "xgboost", "lightgbm", "catboost", "transformers",
    "datasets", "accelerate", "jupyter", "jupyterlab", "notebook", "ipykernel",
    "mlflow", "wandb", "statsmodels", "spacy", "nltk", "opencv-python",
    "polars", "dask",
)

# Dependency manifests we read (bounded) to look for ML libraries.
DEP_FILES = frozenset({
    "pyproject.toml", "setup.py", "setup.cfg", "Pipfile", "environment.yml",
    "environment.yaml",
})

# Map each class to its language family, used to decide monorepo status.
FAMILY = {
    "defect": "python",
    "watcher": "python",
    "silent": "javascript",
    "ironclad": "infra",
    "colorless": "none",
}

# Tie-break order when scores are equal: more specific archetypes win. Lower
# sorts first, so an ML repo (watcher) outranks a generic Python repo (defect).
PRIORITY = {"watcher": 0, "ironclad": 1, "silent": 2, "defect": 3}

STRONG = 3          # score contributed by the first strong signal of a class
MAX_READ = 200_000  # cap (bytes) when reading a dependency manifest


def _read_text(path: str) -> str:
    """Read a small text file, returning "" on any error (binary, perms, ...)."""
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            return fh.read(MAX_READ)
    except OSError:
        return ""


def _dep_present(blob: str, lib: str) -> bool:
    """True if ``lib`` appears as a whole token in a lowercased dependency blob."""
    return re.search(r"(?<![a-z0-9_.-])" + re.escape(lib) + r"(?![a-z0-9_.-])", blob) is not None


def scan(root: str) -> dict:
    """Detect archetype signals under ``root`` and classify the repository."""
    root = os.path.abspath(root)
    signals: dict[str, set[str]] = {c: set() for c in ("defect", "silent", "ironclad", "watcher")}
    ext_counts: dict[str, int] = {}
    dep_blobs: list[str] = []

    for dirpath, dirnames, filenames in os.walk(root):
        # Prune ignored directories in place so os.walk skips them entirely.
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]

        base = os.path.basename(dirpath)
        if base == "terraform":
            signals["ironclad"].add("terraform/ directory")
        if base in ("notebooks", "models", "experiments"):
            signals["watcher"].add(f"{base}/ directory")

        for fn in filenames:
            low = fn.lower()
            _, ext = os.path.splitext(fn)
            ext = ext.lower()
            if ext:
                ext_counts[ext] = ext_counts.get(ext, 0) + 1

            is_req = low.startswith("requirements") and low.endswith(".txt")

            # --- defect (python) ---
            if fn in ("pyproject.toml", "setup.py", "setup.cfg", "Pipfile",
                      "poetry.lock", "tox.ini") or is_req:
                signals["defect"].add(fn)

            # --- silent (typescript / javascript) ---
            if (fn in ("package.json", "tsconfig.json", "pnpm-lock.yaml", "yarn.lock",
                       "angular.json", "svelte.config.js", "deno.json", "bun.lockb")
                    or low.startswith("next.config.")
                    or low.startswith("vite.config.")
                    or low.startswith("nuxt.config.")):
                signals["silent"].add(fn)

            # --- ironclad (infra / IaC) ---
            if fn == "Dockerfile" or low.startswith("dockerfile."):
                signals["ironclad"].add("Dockerfile")
            elif fn in ("docker-compose.yml", "docker-compose.yaml", "compose.yml",
                        "compose.yaml", "Chart.yaml"):
                signals["ironclad"].add(fn)
            elif ext in (".tf", ".tfvars", ".hcl"):
                signals["ironclad"].add(f"*{ext}")

            # --- watcher (data / ML) ---
            if ext == ".ipynb":
                signals["watcher"].add("*.ipynb")
            elif ext in (".parquet", ".h5", ".hdf5", ".ckpt", ".pkl", ".pt",
                         ".onnx", ".safetensors"):
                signals["watcher"].add(f"*{ext} (model/data artifact)")

            # Collect dependency manifests to scan for ML libraries.
            if fn in DEP_FILES or is_req:
                blob = _read_text(os.path.join(dirpath, fn))
                if blob:
                    dep_blobs.append(blob.lower())

    # ML dependency detection across all manifests found.
    depblob = "\n".join(dep_blobs)
    for lib in ML_LIBS:
        if _dep_present(depblob, lib):
            signals["watcher"].add(f"{lib} (dependency)")

    return _classify(signals, ext_counts, root)


def _classify(signals: dict[str, set[str]], ext_counts: dict[str, int], root: str) -> dict:
    """Turn raw signals into scores, a class list, primary, and monorepo flag."""
    scores: dict[str, int] = {}
    for cls, sig in signals.items():
        if sig:
            scores[cls] = STRONG + (len(sig) - 1)

    # Weak extension-prevalence bonus (never enough to create a class alone).
    if ext_counts.get(".py", 0) >= 3:
        scores["defect"] = scores.get("defect", 0) + 1
    js = sum(ext_counts.get(e, 0) for e in (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"))
    if js >= 3:
        scores["silent"] = scores.get("silent", 0) + 1

    classes = sorted(
        (c for c, s in scores.items() if s >= STRONG),
        key=lambda c: (-scores[c], PRIORITY.get(c, 9)),
    )

    if not classes:
        primary, families, monorepo = "colorless", [], False
        classes = ["colorless"]
    else:
        primary = classes[0]
        families = sorted({FAMILY[c] for c in classes})
        monorepo = len(families) >= 2

    return {
        "path": root,
        "primary": primary,
        "classes": classes,
        "families": families,
        "monorepo": monorepo,
        "scores": {c: scores[c] for c in sorted(scores, key=lambda c: -scores[c])},
        "signals": {c: sorted(s) for c, s in signals.items() if s},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="scan.py",
        description="Detect a repository's deck-builder class from its files.",
    )
    parser.add_argument("path", nargs="?", default=".", help="repo root to scan (default: .)")
    args = parser.parse_args(argv)

    if not os.path.isdir(args.path):
        print(f"scan.py: not a directory: {args.path}", file=sys.stderr)
        return 2

    print(json.dumps(scan(args.path), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
