---
description: Run the project's test suite and triage any failures. Use when asked to test, verify, or check that changes pass.
---

# Run tests

1. Detect the runner (pytest is typical for a Defect: check `pyproject.toml`
   `[tool.pytest]`, `tox.ini`, or a `tests/` directory).
2. Run the full suite (e.g. `python -m pytest -q`). Prefer the project's
   documented command if one exists.
3. If anything fails, summarize each failure: the test name, the assertion,
   and the most likely cause. Fix the root cause, not the test, unless the
   test itself is wrong.
4. Re-run until green, then report a one-line pass/fail summary.
