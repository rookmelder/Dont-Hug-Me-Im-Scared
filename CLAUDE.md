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
- **Scope level.** Each engagement's `SCOPE.md` carries a **Level** (1 recon · 2 scan · 3 exploit · 4 god-mode;
  definitions in `agent/scope_levels.json`). Ask the user which level at the start and write it into `SCOPE.md`
  (they confirm the edit). The hooks enforce it on **the workers only** (executor runs and `exec_allow`): a recognised tool
  above the level, or DoS/destructive tooling below level 4, is refused; level 4 lifts every gate. Default to the
  lowest level that does the job, and ask the user before raising it. Your own Bash commands are never blocked by
  the level hooks (the user wants you able to run every command); you still keep to `SCOPE.md` targets yourself.
- **Among workers, only the `executor` base may run commands.** builder, tester, reviewer and scribe stay
  command-less (a hard invariant in `delegate.py`). You, the Lead, may run tools directly from your own Bash,
  dispatch the executor for the allowlisted tools, or run HexStrike over MCP. Review anything destructive (exploit,
  write, brute force, DoS-like, persistence) BEFORE it runs, and stay inside `SCOPE.md` whichever way you run it.
- **Never exfiltrate.** Engagement data and any loot stay on the isolated VM and in the report. `private: yes` stays
  on; `.env`/keys/credentials are denied to every worker.

**New engagement?** Use the **new-engagement** skill. In short: start it from the skeleton: `cp -r engagements/_TEMPLATE engagements/<name>`, then fill in
`engagements/<name>/GOAL.md` and `engagements/<name>/SCOPE.md`. If the root `PROJECT.md` is missing or says
"NOT FILLED IN YET", copy it from `PROJECT.example.md` — the **new-engagement** skill walks through every step.

## Roles and workers
A worker = a **model** + a **harness** that lets it read and write files here. Two modes (`mode:` in `PROJECT.md`):
- **full** (default): **agy** (Google Antigravity CLI: Gemini, Claude Opus/Sonnet, gpt-oss) and **Codex CLI** (GPT on
  the user's ChatGPT plan). Claude entries in a chain are skipped.
- **claude**: for people without agy or Codex. Workers are headless **Claude Code** (`claude -p`, the `claude:<model>`
  entries: haiku / sonnet / opus) on the user's Claude plan; agy and Codex entries are skipped. They run with
  `--safe-mode --restricted` (no CLAUDE.md, no hooks, no project settings), only their base's tools, nothing that asks.
No API keys either way. Only the **executor** base runs commands; every other base is command-less.
- **Authorisation banner.** Every worker task begins with an authorisation preamble (`AUTH_PREAMBLE` in
  `delegate.py`): it states this is authorised, consent-based, in-scope lab work so a worker model does not refuse
  or hedge a legitimate security task. It does **not** loosen scope — the one hard rule it repeats is to act only on
  the task's authorised targets and nothing else.

- A role is `agent/roles/<name>.md`: `base` (builder | tester | reviewer | scribe | executor | **researcher**),
  `models` (the chain of `agy:<model>` / `codex:<model>[:<effort>]` / `claude:<model>[:<effort>]`, first = main;
  unavailable or other-mode workers are skipped, busy/quota errors move on to the next), `does`.
- **Researcher** base: the only one with **web access** (search + read pages), no files, no commands. It must never put
  an IP, hostname or engagement name in a search/URL: `delegate.py` stops it live if it does (WEB LEAK, exit 4), and
  stops any other base that touches the web. Every fact needs its source.
- Cyber roles: **host-researcher** (researcher: one scanned host from `recon.py research`: what it is, value, which
  CVEs really apply, JSON out), **cve-researcher** (researcher: one-off CVE checks for a service list),
  **recon-analyst** (scribe: raw tool output -> short findings), **exploit-builder** (builder: a PoC for one vuln, for
  you to review), **executor** (runs allowlisted tools), **security-reviewer** (reviewer: audits a PoC before it runs),
  **finding-scribe** (scribe: one confirmed finding into `templates/finding.yaml`), **report-scribe** (the report).
  Generic helpers: builder, tester, reviewer.
- **Among workers, only the executor runs commands**, ONLY the tools in `PROJECT.md` `exec_allow`. Every program in
  a command must be on it; commands are checked live and a breach, loop or going over `--max-commands` stops the
  worker (exit 4). In claude mode Claude Code's own permission rules also limit its Bash to those tools.
- Tester and reviewer runs need `--after <builder run id>` or `--after lead`: full mode skips the builder's model
  family (gemini / claude / gpt); claude mode (one family) skips the builder's model (Sonnet's work is checked by Opus).
- **Private project** (`private:` in `PROJECT.md`; anything but `no` counts as private): agy, Codex and Claude
  (`private_ok`).
- Opus is allowed as an agy worker (`claude-opus-4-6-thinking`): use it for the thinking roles (research, security
  review, hard PoCs). Sonnet may build too.
- Models for new roles: `agent/MODELS.md`. Models, families and harness rules the script knows: `agent/models.json`.

## Recon pipeline (scan -> hosts -> research -> rank -> split the work)
Needs SCOPE level 2 (scan) or higher: discover and scan are active (recon.py warns at level 1). You never read raw
scan output. `agent/recon.py` (settings and scoring in `agent/recon.yaml`) does the mechanical part:
1. `python agent/recon.py discover` → nmap host discovery on every SCOPE.md target; raw output in
   `engagements/<name>/scans/`; one `hosts/<ip>/host.yaml` per live in-scope host. Hosts outside SCOPE.md are listed
   under `out_of_scope` in `hosts/index.yaml` and never scanned: tell the user.
2. `python agent/recon.py scan` → one full port/version/vulners scan per host, `parallel` at a time; searchsploit
   per service; CVEs only from tool output. (`all` = discover + scan. `import FILE.xml` = an nmap XML you ran.)
3. `python agent/recon.py research` → one task per scanned host (labels like `host-03`, never IPs) + the
   `delegate.py --role host-researcher ... --schema agent/schemas/host-research.json` commands. Run them in the
   background (the worker cap queues them), then `python agent/recon.py merge <label> <run id>` for each: the result
   goes into `host.yaml`; CVEs without a source are dropped.
4. `python agent/recon.py status` → the ranked table. The score is a formula (worst CVSS, public exploit, CISA KEV,
   services, role such as domain controller, the researcher's value); tiers in `recon.yaml`.
5. Split the work by tier:
   - **big fish**: you and the user together, step by step.
   - **medium**: the strongest workers: `codex:gpt-6-astra:high` / agy Opus (exploit-builder, security-reviewer).
   - **small**: agy Opus/Sonnet or Gemini Flash; claude mode: Sonnet.
   Every exploit PoC still gets `security-reviewer` AND your own review before the executor runs it, whatever the tier.
6. Each confirmed finding → `finding-scribe` fills a copy of `templates/finding.yaml` in `findings/`; you check it.

## Team size (the worker cap)
At most `max_agy` (default 3), `max_codex` (2) and `max_claude` (3) workers at once (`PROJECT.md`). `delegate.py`
enforces it: a run past the cap waits for a free slot (shown in the live log), so you can start a whole research
queue in the background. Why a cap at all: agy's 5-hour pool and the ChatGPT/Claude plan limits run out faster with
more at once (busy errors), and you have to review everything they return. nmap scans by `recon.py` are not workers:
their own `parallel` setting. Never two workers on the same files.
- **Tiny** (<30 lines, or faster to write than to explain): do it yourself.
- **Small** (1 file): 1 worker → you check and review.
- **Medium** (2-4 files): spec → 2 builders in parallel (different harnesses) → full check → checks by risk → fix, commit.
- **Large** (5+ files): write `SPEC.md` first → builders in waves (up to the worker cap) → integrate → checks by risk per part → scribe → final review.
- **Checks by risk** (give every piece a risk in the plan): low = the script's check + your review; medium = a tester
  OR a reviewer; high (any PoC/exploit that will run, anything destructive) = `security-reviewer` AND your own review
  of the code before the executor touches a target.

## Running a worker (from the project root, in the background: 1-8 minutes)
```bash
python agent/delegate.py --role builder --task-file .worker/t1.md --part shop --files src/shop.py --include src/shop.py
```
- Always give `--files` (what the task may change); tester/reviewer need `--after <run id | lead>`.
- **Live view (always on):** every run streams readable lines to `.worker/live.log` and keeps its prompts + full raw
  output in `.worker/run-<id>.log`. The user watches with `tail -f .worker/live.log`; tell them that command when a
  worker starts. Don't read those logs yourself (token cost): read the summary, and grep the run log only to debug.
- Flags, secret-path rules, exit codes (0 ok, 2 input, 3 timeout, 4 blocked, 5 empty, 6 worker error, 7 check failing),
  executor budgets: the **running-workers** skill. Engagement routine: the **engagement-loop** skill.
- Hooks (`.claude/hooks/`) enforce the hard rules: scope gate on executor/HexStrike, no AI attribution, no
  engagement data in git, no AGENTS.md/GEMINI.md. Editing SCOPE.md is allowed but asks for your confirmation every
  time (settings.json). A block message is the rule talking: fix the cause, don't route around it.

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