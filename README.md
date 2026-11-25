# DHMIS: an AI pentest team, Claude leading

A working folder for an **authorised** penetration-testing engagement, where **Claude leads** and **cheaper AI models
do the work**. It is the cyber fork of the [Multi-Agent](https://github.com/rookmelder/Multi-Agent) template: same
safety engine, plus one new capability — an **executor** that can run security tools — kept in its own repo so that
command-running never lands in your safe app/game projects.

> ## ⚠️ Authorisation first — read your engagement's `SCOPE.md`
> This tool runs scanners and exploits. Use it **only** against systems you own or have **written permission** to
> test: your homelab, a Metasploitable VM, a TryHackMe/HTB box on your own account. Each engagement's
> `engagements/<name>/SCOPE.md` lists the authorised
> targets; **every run reads it, and nothing outside it is ever touched.** Testing systems you are not authorised to
> test is illegal. Run the whole thing on an isolated VM (Kali); nothing leaves it.

## The idea in one paragraph

Claude (in Claude Code) is the **boss**: it reads the goal and scope, plans, writes exact instructions, checks every
result, and keeps the write-up. The work — summarising scans, researching CVEs, writing a PoC, running a tool — is
handed to **cheaper AI models** ("workers") on subscriptions you already have. Workers are fast but make mistakes, so
nothing they do is trusted until Claude has checked it. Only one kind of worker, the **executor**, is allowed to run
commands at all, and only an allowlisted set, against only the authorised targets.

## Setting up (on the Kali VM)

1. Clone this repo onto the isolated VM:
   ```bash
   git clone https://github.com/rookmelder/cyber-agent.git
   cd cyber-agent
   ```
2. Set up the tools (you don't need everything): see [agent/setup/README.md](agent/setup/README.md). No API keys —
   workers run through **agy** (Google AI Pro) and **Codex** (ChatGPT plan). For live tool-running, install
   **HexStrike** and connect Claude over MCP: [agent/setup/hexstrike.md](agent/setup/hexstrike.md).
3. Start an engagement from the skeleton: `cp -r engagements/_TEMPLATE engagements/<name>` (one folder per
   engagement, git-ignored). Fill in `engagements/<name>/SCOPE.md` (authorised targets + hard rules — **do this
   before anything runs**) and `engagements/<name>/GOAL.md` (what you want tested, in your own words).
4. Copy the project template to the repo root: `cp PROJECT.example.md PROJECT.md` (Claude fills it in next; the
   filled copy stays local and is never committed).
5. Open the folder in Claude Code and say "let's start". Claude confirms which engagement is active, checks which
   worker tools you have, confirms scope, proposes the roles, and fills in `PROJECT.md` (the check command, the
   executor allowlist, worker notes).
6. Then ask Claude for work ("enumerate services on the box"). It plans, hands pieces out, checks them, and writes up.

## The pieces

| Piece | What it is, simply |
|---|---|
| **Lead** | Claude. Plans, checks, decides, writes the report. Can also run HexStrike tools directly over MCP. |
| **Worker** | A cheaper AI model that does one small, clearly described job. |
| **Model** | The "brain" (Gemini, GPT, Claude Sonnet, ...). On its own a model can only send back text. |
| **Harness** | The program that lets a model act on the VM: **agy** (Google's Antigravity CLI) or **Codex CLI** (OpenAI). It asks the model what it wants to do, checks if it's allowed, and does it. |
| **Role** | A job description for a worker: what it does, which models may do it, and its rules. |
| **`agent/delegate.py`** | The one script that sends a job to a worker: picks the model, adds the rules, runs it safely, logs it, reports back. |
| **HexStrike** | An MCP server that exposes security tools (nmap, nuclei, ...) to the Lead and the executor. |

## Roles

Every role is one small file in `agent/roles/`. It has a **base** (which decides what it is allowed to do), a
**model chain** (first choice, then fallbacks), and a few **rules**.

| Base | Allowed to |
|---|---|
| builder | make and change files |
| tester | write tests/checks (only in the test folder) |
| reviewer | read only, never change anything |
| scribe | write documents (`.md`) only |
| **executor** | **run an allowlist of commands (or HexStrike over MCP)** — the only base that runs anything |

The cyber roles:

| Role | Base | What it does | Models (1st → fallback) |
|---|---|---|---|
| `recon-analyst` | scribe | Turns big scan output into a few short findings | Gemini Flash Low → GPT-6 Luna |
| `cve-researcher` | reviewer | Ranks the CVE data the Lead supplies against the target (the Lead does the lookup) | GPT-6.1 Sol → Claude Sonnet |
| `exploit-builder` | builder | Writes a PoC for one vuln, for the Lead to review | GPT-6.1 Sol → Gemini Flash Medium |
| `executor` | executor | Runs the allowlisted tools / HexStrike | GPT-6.1 Sol → Gemini Flash Medium |
| `security-reviewer` | reviewer | Audits a PoC/change for safety before it runs | GPT-6 Astra → Claude Sonnet |
| `report-scribe` | scribe | Writes the findings report, logs durable results | Gemini Flash Low → GPT-6 Luna |

Generic helpers (builder, builderplus, tester, reviewer, scribe, debugger, mapper) also remain. A tester or reviewer
never uses the same model family as the work it checks: `delegate.py` skips that family. Full routing and ratings:
[agent/MODELS.md](agent/MODELS.md). To make your own role, copy [templates/roles/ROLE-TEMPLATE.md](templates/roles/ROLE-TEMPLATE.md).

## The executor: the one thing that runs commands

Every other base is command-less (the safety engine inherited from the template). The executor inverts that, under
tight controls that `delegate.py` enforces:

- **Allowlist.** It runs only the binaries in `PROJECT.md` `exec_allow` (e.g. `nmap`), or HexStrike tools over MCP.
  Any command whose binary isn't on the list is flagged as a scope breach (exit 4). An empty allowlist runs nothing.
- **Scope.** It must act only on the targets in `SCOPE.md`. Read-only enumeration first; anything destructive waits
  for the Lead.
- **Budget and loop detection.** Capped at `--max-commands` (default 100) per run; a run that repeats the same
  command is stopped so the Lead changes tack.
- **Logged.** Every command and its result go into the run's `.worker/run-*.json`, so nothing executes unseen.
- **agy** additionally gates commands through agy's own global allowlist; **Codex** workers run the binaries directly
  (they can't reach MCP, since their user config is stripped for safety).

## What happens when Claude hands out a job

1. Claude writes a short task: the goal, the in-scope target, the exact step, the one tool.
2. `delegate.py` adds the role's rules and the notes from `PROJECT.md`, and pastes in the files the worker needs.
3. It starts the worker with **only the tools its role allows**, in a sandbox: no touching anything outside the
   project, no git, no web, no reading secret files — and **no commands unless it is the executor**.
4. The worker does its piece and ends with a short report (the executor ends with **done** or **ask**).
5. Claude checks the summary (`files:`, `exec:`, the allowlist/loop flags), verifies the work, and writes the report.
   Raw scan output always goes through the cheap `recon-analyst` first, never straight to the Lead.

## Money, limits and privacy

| Tool | Costs | Limit |
|---|---|---|
| Claude | Your Claude plan | Plan limits; kept for planning, checking and running HexStrike |
| agy | Google AI Pro plan | Resets every 5 hours; ~20 worker jobs use 6-7% of a window |
| Codex | Your ChatGPT plan | The plan's Codex limits (shared with your own Codex use) |
| HexStrike | Free | Runs on the Kali VM |

- **Privacy:** `private: yes` stays on — engagement data must not train cloud models (agy and Codex only; turn off
  "Improve the model for everyone" in ChatGPT). Workers never get `.env`, keys or credentials. Nothing leaves the VM.

## The knowledge map

`knowledge/` keeps the engagement's memory: small linked notes (one per system, finding or decision) plus a running
findings log. `report-scribe` appends durable results to [`knowledge/findings/findings.md`](knowledge/findings/findings.md)
so later runs read past results — the lightweight version of a long-run agent's memory. Search it with
`python agent/check_docs.py --find <words>`.

## The files

| File / folder | What it is |
|---|---|
| `engagements/<name>/SCOPE.md` | **Authorisation and targets.** Per engagement, git-ignored. Every run reads it; nothing outside it is touched. |
| `engagements/<name>/GOAL.md` | **You write this:** what to test this engagement. Per engagement, git-ignored. |
| `engagements/` | Per-engagement data (scans, findings, loot, report, notes) + its GOAL/SCOPE. Git-ignored; see `engagements/README.md`. |
| `PROJECT.md` | Claude fills this in (privacy, check command, executor allowlist, worker notes). Lives at the root for `delegate.py`; copied from `PROJECT.example.md`, git-ignored. |
| `SETUP.md` | Made by `agent/check_setup.py`: what works on this VM (not committed). |
| `CLAUDE.md` | The rulebook Claude reads at the start of every session. |
| `agent/roles/` | The roles in use. `agent/bases/` | the core rules per base (incl. `executor.md`). |
| `agent/delegate.py` | Runs a worker. `agent/check_setup.py` checks your setup. `agent/check_docs.py` checks the notes. |
| `agent/MODELS.md` | Which model to pick per role, with ratings. `agent/LIMITS.md`: cost and limits per tool. |
| `agent/models.json` | The models, model families and harness rules `delegate.py` knows. |
| `agent/setup/` | How to install and sign in to each tool, including `hexstrike.md`. |
| `agent/notes/` | Measurements and lessons about the setup itself, one small note each. |
| `knowledge/` | Generic, reusable knowledge map and lessons (in git). Real engagement findings go in `engagements/<name>/`. |
| `templates/` | Role template and note templates. |
| `.agents/agents/` | Trimmed tool sets for agy workers (incl. `w-executor`, the one with a command tool). |
| `.worker/` | Scratch space for tasks, results and logs (not committed). |

## Known weak spots

- Workers make mistakes; that's expected — Claude checks everything, and reviews any PoC before the executor runs it.
- Workers can't create folders and (except the executor) can't run commands; Claude does those parts.
- Codex executor workers can't reach MCP (user config is stripped), so HexStrike runs via the Lead or an agy executor.
- The exact agy terminal-tool id and MCP wiring depend on your agy build — confirm them against agy's docs before
  trusting an agy executor (see `.agents/agents/w-executor.md` and `agent/setup/hexstrike.md`).
- If a file called `AGENTS.md` or `GEMINI.md` is in the project, agy/Codex loads it into every worker. Don't add one.
