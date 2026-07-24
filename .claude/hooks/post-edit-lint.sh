#!/usr/bin/env bash
# Non-blocking: lints a just-edited Python file with ruff, if available.
#
# Always exits 0 — this hook only warns, it never blocks a tool call. That
# matches this repo's own Ascension 0 philosophy (hooks warn, they don't
# block; see ARCHITECTURE.md). Degrades silently if jq/ruff aren't installed.
set -u

command -v jq >/dev/null 2>&1 || exit 0

file=$(jq -r '.tool_input.file_path // empty' 2>/dev/null)

case "$file" in
  *.py)
    if command -v ruff >/dev/null 2>&1; then
      ruff check "$file" || true
    fi
    ;;
esac

exit 0
