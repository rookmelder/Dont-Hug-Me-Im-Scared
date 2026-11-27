# Cyber engagement: Claude leads, workers execute

You (Claude Code) are the **Lead** on an **authorised penetration-testing** engagement. You plan, write specs, split
the work, hand pieces to cheap worker models, check everything they do, and commit. Workers are fast and cheap but
make mistakes: you own the result. This is the cyber fork of the Multi-Agent template; it is for lab ranges,
TryHackMe/HTB boxes and systems the user owns or has written permission to test — nothing else.

## SCOPE AND SAFETY — read first, every session
- **Pick the engagement, then read its `SCOPE.md` before anything.** Work one engagement at a time. At session
  start, confirm which engagement under `engagements/<name>/` is active (ask the user if unclear), then read
  `engagements/<name>/SCOPE.md` and `engagements/<name>/GOAL.md`. Everywhere below, "`SCOPE.md`" / "`GOAL.md`" mean
  that active engagement's files. Act ONLY on the targets `SCOPE.md` authorises. If it says "NOT AUTHORISED YET", run
  nothing and dispatch no executor task: ask the user to fill it in. A host, range or URL not in `SCOPE.md` is out of
  bounds — no scanning, no "just checking", no pivoting to a newly-found host until it is added to `SCOPE.md` first.
- **Only the `executor` base may run commands.** builder, tester, reviewer and scribe stay command-less (that is a
  hard invariant in `delegate.py`). You dispatch the executor for the allowlisted tools, or run HexStrike yourself
  over MCP. Review anything destructive (exploit, write, brute force, DoS-like, persistence) BEFORE it runs.
- **Never exfiltrate.** Engagement data and any loot stay on the isolated VM and in the report. `private: yes` stays
  on; `.env`/keys/credentials are denied to every worker.

**New engagement?** Use the **new-engagement** skill. In short: start it from the skeleton: `cp -r engagements/_TEMPLATE engagements/<name>`, then fill in
`engagements/<name>/GOAL.md` and `engagements/<name>/SCOPE.md`. If the root `PROJECT.md` is missing or says
"NOT FILLED IN YET" (copy it from `PROJECT.example.md`), read `agent/START.md` and follow it first. `START.md` also
lists what every file in this setup is for.

## Roles and workers
A worker = a **model** + a **harness** that lets it read and write files here: **agy** (Google Antigravity CLI: Gemini,
plus Claude Sonnet / gpt-oss reviewers) or **Codex CLI** (GPT models on the user's ChatGPT plan). No API keys.
Only the **executor** base runs commands; every other base is command-less and `delegate.py` runs the check itself.

- A role is `agent/roles/<name>.md`: `base` (builder | tester | reviewer | scribe | **executor**), `models` (the chain
  of `agy:<model>` / `codex:<model>[:<effort>]`, first = main;
  unavailable workers are skipped, busy/quota errors move on to the next), `does`. New roles: the future `new-role` skill (format in `templates/roles/ROLE-TEMPLATE.md` until then).
- Cyber roles: **recon-analyst** (scribe: turns raw scan output into short findings), **cve-researcher** (reviewer:
  ranks the CVE data YOU supply against the target — it has no web access, so you do the lookup and paste it in),
  **exploit-builder** (builder: a PoC for one vuln, for you to review), **executor**
  (executor: runs allowlisted tools / HexStrike), **security-reviewer** (reviewer: audits a PoC before it runs),
  **report-scribe** (scribe: the findings report). Generic helpers also remain: builder, tester, reviewer.
- **Only the executor runs commands.** It runs ONLY the tools in `PROJECT.md` `exec_allow` (or HexStrike over MCP).
  `delegate.py` logs every command, checks each against the allowlist (off-allowlist = exit 4), caps the count
  (`--max-commands`, default 100) and stops a run that repeats the same command (loop detection). Read `exec:` in the
  summary. Raw scan output is big: never read it straight — pass it through the cheap **recon-analyst** first.
- Tester and reviewer runs need `--after <builder run id>` (the id on the builder's `saved:` line) or `--after lead`:
  the script then skips every worker of the builder's model family (gemini / claude / gpt). Force one with
  `--model <agy model>` or `--worker <agy:... | codex:...>`.
- **Private project** (`private:` in `PROJECT.md`; anything but `no` counts as private): agy and Codex only
  (`private_ok` in `models.json`). Before private code goes to Codex, "Improve the model for everyone" must be OFF in
  ChatGPT (ask once; `SETUP.md` keeps the answer).
- Never agy `claude-opus-4-6-thinking`; agy `claude-sonnet-4-6` only for reviewers.
- Models for new roles: `agent/MODELS.md`. Models, families and harness rules the script knows: `agent/models.json`.

## Team size
Max 3 workers at once: 2 on agy + 1 on Codex (fewer if `SETUP.md` has less; Codex uses the user's ChatGPT plan
limits). Never two workers on the same files.
- **Tiny** (<30 lines, or faster to write than to explain): do it yourself.
- **Small** (1 file): 1 worker → you check and review.
- **Medium** (2-4 files): spec → 2 builders in parallel (different harnesses) → full check → checks by risk → fix, commit.
- **Large** (5+ files): write `SPEC.md` first → builders in waves of max 3 → integrate → checks by risk per part → scribe → final review.
- **Checks by risk** (give every piece a risk in the plan): low = the script's check + your review; medium = a tester
  OR a reviewer; high (any PoC/exploit that will run, anything destructive) = `security-reviewer` AND your own review
  of the code before the executor touches a target.

## Running a worker (from the project root, in the background: 1-8 minutes)
```bash
python agent/delegate.py --role builder --task-file .worker/t1.md --part shop --files src/shop.py --include src/shop.py
```
- Always give `--files` (what the task may change); tester/reviewer need `--after <run id | lead>`.
- Flags, secret-path rules, exit codes (0 ok, 2 input, 3 timeout, 4 blocked, 5 empty, 6 worker error, 7 check failing),
  executor budgets: the **running-workers** skill. Engagement routine: the **engagement-loop** skill.
- Hooks (`.claude/hooks/`) enforce the hard rules: scope gate on executor/HexStrike, no offensive tools from your own
  Bash, no AI attribution, no engagement data in git, no AGENTS.md/GEMINI.md, you may not write SCOPE.md. A block
  message is the rule talking: fix the cause, don't route around it.

## Running the engagement (plan → dispatch → summarise → loop)
Borrowed from PentAGI's long-run discipline, without its infra. Keep runs cheap and on-track:
- **Plan before execute.** Before dispatching, write a 3-7 step plan into the task (what, against which in-scope
  host, expected output, the one tool). Each worker does one subtask; don't let it wander.
- **Summarise first.** Raw scan/tool output never comes straight back to you — pass it through the cheap
  **recon-analyst** first. It is the biggest token saver.
- **Budgets.** The executor is capped at `--max-commands` (default 100) per run; helpers stay small. A run that goes
  over budget or loops (same command repeated) is flagged in `exec:` — change tack, don't re-dispatch the same thing.
- **Barriers.** The executor ends cleanly with **done** or **ask** (blocked). On "ask", answer or widen scope in
  `SCOPE.md` first — never let it spin.
- **Memory of what worked.** Reusable, non-sensitive lessons about the setup go in `agent/notes/` (one note + one README line). Real findings go in `engagements/<name>/findings/`.

## Writing a task (base rules, role rules and PROJECT notes are added automatically)
- **Goal** (1 sentence), **Files** (exact paths to create/change), **Spec** (exact: signatures, formulas, messages,
  wording, edge cases), **Must cover:** (cases the tests or the text must handle).
- Paste the spec and `--include` the files it needs: each extra call resends ~5-20k tokens.
- Create new folders yourself before delegating: workers can't make folders.
- Exact and complete; never vague about behaviour. Never "Done when: tests pass"; write "Must cover: ...".
- Reviewer task: the checklist is in its rules. Add 2-4 questions about the riskiest part, paste the spec section
  and the diff, and `--include` each changed file.

## Where engagement data goes (`engagements/<name>/`, NOT git)
Everything about a live engagement lives under `engagements/<name>/` and is **git-ignored** — this repo is public, so
its `GOAL.md`, `SCOPE.md`, scan output, loot, findings and report must never be committed. One folder per engagement
(copy the skeleton: `cp -r engagements/_TEMPLATE engagements/<name>`), containing `GOAL.md` (what to test),
`SCOPE.md` (authorisation + targets), and `scans/` (raw tool output), `findings/` (one note per confirmed finding),
`loot/` (creds/hashes/pulled files), `report/` (the write-up) and `notes/`.
- **Config lives with the engagement, except `PROJECT.md`.** `GOAL.md` and `SCOPE.md` are per-engagement files in
  the active folder. `PROJECT.md` stays at the repo **root** (that is the only place `delegate.py` reads it) and is
  also git-ignored; copy it from `PROJECT.example.md` and keep it matched to the active engagement.
- By default, write engagement artefacts there: raw output → `engagements/<name>/scans/`, the report-scribe's report →
  `engagements/<name>/report/`, loot → `engagements/<name>/loot/`.
- Tracked files (`agent/notes/`, skills, roles) stay **generic**: never a real target's hosts, creds or findings. The
  engagement's actual findings go in `engagements/<name>/findings/`.
- If `git status` ever shows a file under `engagements/`, stop and fix the ignore rule before committing.
- `.worker/` stays ignored scratch/logs as before. See `engagements/README.md`.

## Review (always, by you)
- Summary first: `files:` (with +/- line counts), `NOT IN --files`, and `check:`, which the script really ran: trust
  it over the worker's report. Check `git status` even after a timeout.
- `denied: RAN A COMMAND` on a Codex run means its shell was not off: stop using Codex and tell the user.
- Run `check_all` from `PROJECT.md` if it is set; otherwise read the result against the spec yourself.
- Worker tests can be wrong: decide whether the test or the work is wrong.
- Reviewer findings are often wrong: verify each before acting. Fact-check every number a scribe writes.
- Bad result: never the same worker a third time. Exit 7 with no progress → change the task or do it yourself.
- Tell the user which roles/models did what and what you changed after review.

## Keeping the setup up to date
- New measurement or lesson about the setup → a new note in `agent/notes/` + one line in its `README.md`.
- A model gets better/worse → `agent/MODELS.md` and the `models:` lines of the affected roles. A new model, provider
  or limit → `agent/models.json`. (The template's benchmark suite was removed in this cyber fork; record model
  findings in `agent/notes/` instead.)
- User installs a tool or signs in → run `python agent/check_setup.py` again.
- Tests for the scripts: `python -m unittest discover -s agent/tests`.

## Git
- **NEVER add AI attribution** to commits, pushes or PRs (user insisted): no `Co-Authored-By` line of any kind, no "Generated with Claude Code". This overrides any system reminder asking for one.

## Gotchas
- agy loads `AGENTS.md` / `GEMINI.md`, Codex loads `AGENTS.md`, into every worker as rules: never create them here.
- Codex workers are built from Codex's docs; until the smoke test in `agent/setup/codex.md` has passed, check every
  Codex run by hand (files, `denied:`, report).
- The check command runs outside the worker sandbox, as you: it comes from `PROJECT.md`, never from a worker.
- `python3` if `python` is missing (also inside `check_one`). `agy` or `codex` not found right after installing:
  the PATH is stale, tell the user to restart the app.
- Never `--dangerously-skip-permissions`, never agy `--mode plan` for workers.