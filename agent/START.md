# Starting a project (for the Lead)

Read this once per project. Do the steps in order; skip what is already done.

1. **Setup.** Run `python agent/check_setup.py` (it writes `SETUP.md`). Ask the user the
   "Confirmed by the user" questions in it once and fill them in. Missing tools: point to `agent/setup/README.md`;
   it is fine to start with what exists.
2. **Engagement + Goal.** Each engagement is its own git-ignored folder under `engagements/`. Start one with
   `cp -r engagements/_TEMPLATE engagements/<name>` (work one engagement at a time; confirm the active name with the
   user). If `engagements/<name>/GOAL.md` says "NOT WRITTEN YET", ask the user to write it there in their own words
   (or tell you, and you write it down in their words). Then ask about everything important it leaves out (depth:
   enumeration only or exploit too? is exploitation authorised, or stop at a PoC?). Add the answers to that `GOAL.md`.
3. **SCOPE (do this before any tool runs).** `engagements/<name>/SCOPE.md` is the authorisation and target list.
   While it says "NOT AUTHORISED YET", run nothing. Confirm with the user: do they own the targets or have written
   permission? Fill in the authorisation, the in-scope hosts/ranges/URLs, the window, and leave the hard rules.
   Nothing outside that list may ever be touched.
4. **Roles.** The cyber roles ship in `agent/roles/`: recon-analyst, cve-researcher, exploit-builder, executor,
   security-reviewer, report-scribe (plus the generic helpers builder, builderplus, tester, reviewer, scribe,
   debugger, mapper). Confirm which this engagement needs and their models; make new ones from
   `templates/roles/ROLE-TEMPLATE.md`. A tester/reviewer role needs two model families.
5. **Project.** Copy the template to the repo root if needed (`cp PROJECT.example.md PROJECT.md`), then fill in
   `PROJECT.md` (about, settings, worker notes) and remove its "NOT FILLED IN YET" line. `PROJECT.md` stays at the
   root (the only place `delegate.py` reads it) and is git-ignored. Keep `private: yes`. Set `exec_allow` to the
   tightest useful allowlist for the executor (start with `nmap`); empty means the executor can run nothing.
6. **Tools.** Install/start HexStrike on the Kali VM and connect the Lead over MCP (`agent/setup/hexstrike.md`). Run
   `python agent/check_setup.py` to confirm which worker CLIs are live. Record model findings in `agent/notes/`.
7. **Knowledge map.** `knowledge/` holds the project's map (one small note per system, finding or decision,
   see `knowledge/README.md`). Keep it for anything bigger than a few files; for a tiny project ask the user
   whether to delete it. Existing code? Make one system note per part before the first task.
8. **Repo.** The project's files live inside this folder (e.g. `src/`, `design/`): `delegate.py` uses this
   folder's git status to see what a worker changed. If `origin` still points at the template repo, ask the user
   for the project's own repo URL.

## The files
| File | Who writes it | What it is |
|---|---|---|
| `engagements/<name>/SCOPE.md` | you + the user | **Authorisation and targets.** Per engagement, git-ignored. Every run reads it; nothing outside it is touched. |
| `engagements/<name>/GOAL.md` | the user | What to test this engagement, in their own words. Per engagement, git-ignored. The source of truth for *what* to do. |
| `PROJECT.md` | you (user approves) | Settings from GOAL.md: privacy, check command, `exec_allow`, worker notes. At the repo root for `delegate.py`; copied from `PROJECT.example.md`, git-ignored. |
| `SETUP.md` | `agent/check_setup.py` | Which worker tools this machine has (git-ignored). |
| `agent/roles/<name>.md` | you (user approves) | The worker roles in use: base type, model chain, extra rules. |
| `agent/bases/<base>.md` | template | Core rules per base (builder, tester, reviewer, scribe, executor). Rarely changed. |
| `agent/delegate.py` | template | The only way to run a worker; the executor is the only base that runs commands. |
| `agent/models.json` | you | The models, model families and harness rules `delegate.py` knows. |
| `agent/MODELS.md` | you | Which model to pick per role, with ratings. |
| `agent/LIMITS.md` | you | What each worker tool costs, its limits and its quirks. |
| `agent/notes/` | you | What we measured and learned about the setup: one note per entry, index in its `README.md`. |
| `engagements/` | you + scribe | Per-engagement data (git-ignored): each `<name>/` holds GOAL/SCOPE + scans, findings, loot, report, notes. |
| `knowledge/` | you + scribe | Generic, reusable knowledge map (in git): small linked notes per system, finding, decision. Keep real targets out. |
| `agent/check_docs.py` | template | Checks `knowledge/` and `agent/notes/` (broken links, orphans, missing files); `--find <words>` searches them. |
| `agent/setup/` | template | How to install and sign in to each tool, including `hexstrike.md` (point the user here). |
| `templates/` | template | `roles/ROLE-TEMPLATE.md` and note templates (`notes/`). |
| `README.md` | template | The whole setup explained for the user in plain words. |
