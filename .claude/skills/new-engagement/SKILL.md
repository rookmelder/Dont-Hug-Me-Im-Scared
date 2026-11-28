---
name: new-engagement
description: "Start a new pentest engagement: scaffold engagements/<name>, GOAL.md, SCOPE.md, PROJECT.md, exec_allow. Use when the user says new engagement / new box / let's start, or the session-start status says no engagement, PROJECT.md not filled in, or SCOPE.md NOT AUTHORISED YET."
argument-hint: "<name>"
---

# New engagement (for the Lead)

Engagement name: $ARGUMENTS (short, e.g. `htb-blue`, `lab-proxmox`). Do the steps in order; skip what is done.

1. `python agent/check_setup.py` (writes SETUP.md). Missing tools: `agent/setup/README.md`.
2. `cp -r engagements/_TEMPLATE engagements/<name>` (git-ignored; one engagement at a time).
3. **GOAL.md**: ask the user for it in their words; then ask what it leaves out (enumeration only, or exploit too?
   stop at a PoC?). Write the answers into `engagements/<name>/GOAL.md`.
4. **SCOPE.md is the user's to fill in** (the hooks block you from writing it, and Edit/Write on it asks). Ask: do
   they own the targets or hold written permission, what exactly is in scope, what is the time window? Tell them to
   edit the file, then read it back. **Also ask which level** (1 recon / 2 scan / 3 exploit / 4 god-mode; see
   `agent/scope_levels.json`) and have them set it in SCOPE.md — it gates the workers (not your own commands). While it says
   NOT AUTHORISED YET: no executor run, no HexStrike call.
5. `cp PROJECT.example.md PROJECT.md` if missing; fill it in; delete the "NOT FILLED IN YET" line. Keep `private: yes`.
   **Mode:** ask whether they have agy and/or Codex (`mode: full`) or only Claude (`mode: claude`: workers run on their
   Claude plan).
   Worker cap `max_agy` / `max_codex` / `max_claude`: leave the defaults unless they hit busy errors or want more.
   `exec_allow`: the tightest list that does the job (start with `nmap`; widen one tool at a time).
6. Tools for `agent/recon.py`: `nmap` (required), `searchsploit` (optional, `apt install exploitdb`). Check
   `agent/recon.yaml` (scan commands, parallel scans, scoring) with the user.
7. HexStrike (optional): `agent/setup/hexstrike.md`. Its MCP calls are gated by `guard_mcp.py` against SCOPE.md.
8. Tell the user which hooks now protect the run (see the engagement-loop skill) and what is still manual.

Never put real targets, creds or findings in `agent/notes/` or any tracked file.
