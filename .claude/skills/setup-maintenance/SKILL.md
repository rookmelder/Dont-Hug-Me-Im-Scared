---
name: setup-maintenance
description: "Keeping this setup up to date: roles, model chains, MODELS.md, models.json, editing delegate.py, hooks and settings.json, tool installs, script tests. Use when changing roles/models/hooks/permissions or editing scripts in agent/."
---

# Keeping the setup up to date

## Roles and models
- A role is `agent/roles/<name>.md`: `base` (builder | tester | reviewer | scribe | executor), `models` chain, `does`.
  Format: `templates/roles/ROLE-TEMPLATE.md`. Models for new roles: `agent/MODELS.md`; known models/families:
  `agent/models.json`. Model findings go in `agent/notes/` + one line in its README.
- Never agy `claude-opus-4-6-thinking`; agy `claude-sonnet-4-6` only for reviewers.

## Editing delegate.py
- Never agy `--dangerously-skip-permissions` or `--mode plan`. Only the executor base may have a command tool; keep that invariant.
- Secret paths: exit 4 and denied to every worker. Keep it that way.

## Hooks and settings (`.claude/`)
- `settings.json` is shared: permissions, attribution off, hook wiring. Personal settings -> `settings.local.json` (git-ignored).
- Hooks read JSON on stdin; exit 2 blocks and shows stderr to Claude. Changes need a new session. Run with `python3`.
  - `_scope.py`: shared: active engagement, authorised?, target in SCOPE.md? Fails closed.
  - `guard_files.py` (Write|Edit): no AGENTS.md / GEMINI.md.
  - `guard_shell.py` (Bash): attribution, `--files`, no engagement/PROJECT/GOAL/SCOPE in git,
    executor scope gate, no offensive tools straight from Bash, no shell writes to SCOPE.md.
  - `guard_mcp.py` (`mcp__hexstrike*`): authorised scope + in-scope targets only.
  - `session_start.py`: engagement / PROJECT / SETUP status, never targets.
- Git hooks `agent/githooks/` (commit-msg: attribution; pre-commit: engagement data): `check_setup.py` sets
  `core.hooksPath` when unset.
- Limits: the Bash hooks see only the Lead's commands, not what a worker's executor runs (delegate.py's allowlist does),
  and target matching is a regex over the command text, a safety net, not proof. Review before you run.
- Tests: `python3 -m unittest discover -s agent/tests` (`test_hooks.py` covers every hook).

## Tools and sign-ins
User installs a tool or signs in -> `python agent/check_setup.py` again. PATH stale after install: restart the app.
