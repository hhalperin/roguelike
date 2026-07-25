#!/usr/bin/env python3
"""spire :: scan.py — deterministic repo stack detector.

Walks a target repository and detects its roguelike "class" (archetype) purely
from the files present. Detection rules live in ``classes/detection.json`` so
adding an archetype is a data change, not a code change. Standard library
only: no third-party dependencies, no network, no LLM. Emits a JSON summary
on stdout that the ``/spire`` skill interprets to deal a starter deck.

Usage
-----
    python scan.py [PATH]        # PATH defaults to the current directory
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

STRONG = 3          # score contributed by the first strong signal of a class
MAX_READ = 200_000  # cap (bytes) when reading a dependency manifest

_DETECTION_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "classes", "detection.json",
)


def _load_detection() -> dict:
    with open(_DETECTION_PATH, encoding="utf-8") as fh:
        return json.load(fh)


_DETECTION = _load_detection()
ML_LIBS = tuple(_DETECTION["ml_libs"])
DEP_FILES = frozenset(_DETECTION["dep_files"])
CLASS_SPECS = _DETECTION["classes"]

# Public maps used by tests and deck.py — derived from detection.json.
FAMILY = {name: spec["family"] for name, spec in CLASS_SPECS.items()}
PRIORITY = {
    name: spec["priority"]
    for name, spec in CLASS_SPECS.items()
    if not spec.get("fallback")
}
CLASS_NAMES = {
    name: spec["display_name"]
    for name, spec in CLASS_SPECS.items()
}


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
    scorable = [c for c, s in CLASS_SPECS.items() if not s.get("fallback")]
    signals: dict[str, set[str]] = {c: set() for c in scorable}
    ext_counts: dict[str, int] = {}
    dep_blobs: list[str] = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]

        base = os.path.basename(dirpath)
        for cls, spec in CLASS_SPECS.items():
            if spec.get("fallback"):
                continue
            if base in spec.get("dir_markers", []):
                signals[cls].add(f"{base}/ directory")

        for fn in filenames:
            low = fn.lower()
            _, ext = os.path.splitext(fn)
            ext = ext.lower()
            if ext:
                ext_counts[ext] = ext_counts.get(ext, 0) + 1

            is_req = low.startswith("requirements") and low.endswith(".txt")

            for cls, spec in CLASS_SPECS.items():
                if spec.get("fallback"):
                    continue
                if fn in spec.get("exact_files", []):
                    signals[cls].add(fn)
                if spec.get("requirements_txt") and is_req:
                    signals[cls].add(fn)
                if spec.get("dockerfile") and (fn == "Dockerfile" or low.startswith("dockerfile.")):
                    signals[cls].add("Dockerfile")
                for prefix in spec.get("config_prefixes", []):
                    if low.startswith(prefix):
                        signals[cls].add(fn)
                        break
                label = spec.get("ext_markers", {}).get(ext)
                if label:
                    signals[cls].add(label)

            if fn in DEP_FILES or is_req:
                blob = _read_text(os.path.join(dirpath, fn))
                if blob:
                    dep_blobs.append(blob.lower())

    depblob = "\n".join(dep_blobs)
    for cls, spec in CLASS_SPECS.items():
        if not spec.get("ml_deps"):
            continue
        for lib in ML_LIBS:
            if _dep_present(depblob, lib):
                signals[cls].add(f"{lib} (dependency)")

    return _classify(signals, ext_counts, root)


def _classify(signals: dict[str, set[str]], ext_counts: dict[str, int], root: str) -> dict:
    """Turn raw signals into scores, a class list, primary, and monorepo flag."""
    scores: dict[str, int] = {}
    for cls, sig in signals.items():
        if sig:
            scores[cls] = STRONG + (len(sig) - 1)

    for cls, spec in CLASS_SPECS.items():
        if spec.get("fallback"):
            continue
        bonus = spec.get("ext_bonus") or {}
        if not bonus:
            continue
        if spec.get("ext_bonus_shared"):
            total = sum(ext_counts.get(e, 0) for e in bonus)
            threshold = next(iter(bonus.values()))
            if total >= threshold:
                scores[cls] = scores.get(cls, 0) + 1
        else:
            for ext, threshold in bonus.items():
                if ext_counts.get(ext, 0) >= threshold:
                    scores[cls] = scores.get(cls, 0) + 1

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
        description="Detect a repository's spire class from its files.",
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
