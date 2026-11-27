---
name: running-workers
description: "Flags, paths, secrets and exit codes for agent/delegate.py, executor budgets and Codex/private-project rules. Use when a delegate.py run exits non-zero, a run summary looks odd, or you need a flag beyond the basic command."
---

# Running workers: flags, paths, exit codes

Basic command and hard rules are in `CLAUDE.md`; all flags: `python agent/delegate.py --help`.

## Flags
- `--part <name>`: fills `{name}` in `check_one`; a failure goes back to the worker (`--fix-rounds`, default 2). For a
  reviewer the check runs first and is pasted into its task.
- `--files <files or globs>`: what the task may change; anything else shows under `NOT IN --files`. The shell hook
  refuses runs without it, except reviewer-base and executor roles.
- `--include <files>`: pastes files into the task.
- `--after <run id | lead>`: required for tester/reviewer; skips workers of the builder's model family.
- `--model <agy model>` / `--worker <agy:... | codex:...[:effort]>`: force one worker.
- `--conversation <id>`: follow-up (max 2, then do it yourself).
- `--max-commands <n>`: executor command budget (default 100).

## Paths and secrets
`--include`/`--files` stay inside the project and never name a secret (`.env*`, keys, credentials): exit 4. Every run
denies workers each secret file it finds. settings.json also denies `Read` on them for you.

## Exit codes
| Code | Meaning | What to do |
|---|---|---|
| 0 | ok | Review the summary and files. |
| 2 | bad input | Fix the command. |
| 3 | timeout | `git status`: files often exist. |
| 4 | blocked: path, off-allowlist executor command, or Codex ran a command | Path: fix. `RAN A COMMAND`: stop using Codex, tell the user. |
| 5 | empty answer | Retry once with another worker, or do it yourself. |
| 6 | worker error / quota / none available | `SETUP.md`, `agent/LIMITS.md`; other role/worker. |
| 7 | check still failing | No progress -> change the task or do it yourself. |

Full result: the `.worker/run-<id>.json` named in the summary (`.worker/last.json` = latest).

## Executor
Runs only `exec_allow` binaries (empty = nothing), every command logged, loop detection on. The shell hook (not
delegate.py) additionally refuses an executor dispatch while SCOPE.md is unauthorised or the command names a host/IP
outside it. HexStrike MCP calls get the same gate from `guard_mcp.py`.

## Private projects and Codex
`private:` anything but `no` = private: agy and Codex only (`private_ok`); keep `yes`. Before engagement data goes to
Codex, "Improve the model for everyone" must be OFF in ChatGPT (ask once; SETUP.md keeps the answer). Until the smoke
test in `agent/setup/codex.md` passed, check every Codex run by hand. Max 1 Codex worker at a time.
