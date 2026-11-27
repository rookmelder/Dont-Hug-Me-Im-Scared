# Project — cyber engagement

<!-- Copy this to PROJECT.md at the repo root (cp PROJECT.example.md PROJECT.md) and fill it in. PROJECT.md stays at
     the root (the only place delegate.py reads it) and is git-ignored — never commit the filled-in copy.
     Filled in by the Lead (Claude) from the active engagement's GOAL.md and SCOPE.md, with the user's OK.
     delegate.py reads the "settings" block and pastes "Worker notes" into every worker's task. -->

**Status:** NOT FILLED IN YET

## About (for the Lead)
- **Engagement:** <name> (its config + data live in `engagements/<name>/`)
- **In one sentence:** <what we are testing this engagement, from engagements/<name>/GOAL.md>
- **Targets:** see `engagements/<name>/SCOPE.md` (the authorised list; every run reads it).
- **Where the work lives:** `engagements/<name>/` (git-ignored: scans, findings, loot, report, notes — all real
  engagement data), `.worker/` (scratch, logs).
- **Roles in use:** recon-analyst, cve-researcher, exploit-builder, executor, security-reviewer, report-scribe.
- **Done means (this engagement):** <from engagements/<name>/GOAL.md>

## Settings (read by delegate.py)
Leave a value empty when it doesn't apply. `{name}` stands for the part a worker works on (`--part <name>`).

```settings
check_one:
check_all:
check_dir:
private: yes
exec_allow:
```

- `check_one`: run after a builder/tester on its part. For pentest work the "check" is light: usually empty, and the
  Lead reviews findings and the report by reading. Set it only if a part has a real format/lint check.
- `check_all`: the light check the Lead runs after a worker. Usually empty: the Lead reviews by reading.
- `check_dir`: the only folder a tester may write in. Empty = only the files its task names.
- `private`: keep `yes`. Engagement data must not train cloud models — agy and Codex only, "Improve the model for
  everyone" OFF in ChatGPT.
- `exec_allow`: the ONLY commands the **executor** base may run (binary names, space/comma separated). **Empty = the
  executor may run nothing (fail closed).** Keep it tight; widen one tool at a time.
  Example for a first "enumerate services" run: `exec_allow: nmap`. Later maybe: `nmap nuclei httpx whatweb gobuster`.
  HexStrike tools come in over MCP, not through this list; see `agent/setup/hexstrike.md`.

## Worker notes (pasted into every worker's task: keep it short)
- <lab/VPN only: everything runs on the isolated VM; nothing leaves it>
- <read SCOPE.md; act only on authorised targets; read-only first, destructive waits for the Lead>
- <tool flags/versions to prefer; output format for findings (host, port, service, version, evidence)>
- <known traps for this engagement>
