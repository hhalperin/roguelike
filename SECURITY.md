# Security Policy

## Supported versions

spire is pre-1.0. Security fixes land on the latest `0.x` release.

| Version | Supported |
|---|---|
| 0.2.x | ✅ |
| 0.1.x | ✅ |
| < 0.1 | ❌ |

## Reporting a vulnerability

**Please do not open a public issue for security problems.**

Report privately through GitHub: on the repository's **Security** tab, choose
**Report a vulnerability** (Privately report a vulnerability). Include:

- what the issue is and where (file / component),
- steps to reproduce or a proof of concept,
- the impact you foresee.

We aim to acknowledge a report within **7 days** and to agree on a fix timeline
after triage. Please give us reasonable time to release a fix before any public
disclosure.

## Threat model notes

spire is a Claude Code plugin. Two properties shape its security surface:

- **It writes config into your repository.** `/spire` creates `CLAUDE.md`,
  `.spire/deck.json`, and `.claude/skills/*` in the *target* project. It appends
  to an existing `CLAUDE.md` rather than overwriting, and refuses to re-deal over
  an existing `deck.json`. Reports about unintended writes, overwrites, or path
  traversal are in scope.
- **Its runtime scripts are pure standard library.** `scripts/scan.py` and
  `scripts/deck.py` take no network input and add no third-party dependencies,
  which keeps the runtime supply chain minimal. Reports about unsafe file
  handling or code execution in these scripts are in scope.

Out of scope: vulnerabilities in Claude Code itself, or in optional soft
dependencies such as `claude-agent-sdk` when used only for the reward loop.
