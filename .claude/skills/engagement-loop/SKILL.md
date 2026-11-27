---
name: engagement-loop
description: "The plan -> dispatch -> summarise -> loop routine for running an authorised engagement: executor tasks, recon-analyst triage, risk checks, findings and report. Use when about to dispatch an executor run, triage scan output, review an exploit PoC or write the report."
---

# Running the engagement

## Before a run
- Active engagement confirmed with the user; its SCOPE.md authorised (the session-start hook says if not).
- Write a 3-7 step plan into the task: what, which in-scope host, expected output, the ONE tool. One subtask per run.
- Read-only first. Destructive (exploit, write, brute force, DoS-like, persistence) waits for your review.

## Dispatch
- Scan / enumerate: `python agent/delegate.py --role executor --task-file .worker/tN.md` (the shell hook checks the
  authorisation and that every host/IP in the command is in SCOPE.md; `--files` is not needed for the executor).
  Put raw output in `engagements/<name>/scans/`.
- Never read raw scan output yourself: `--role recon-analyst` first (scribe, cheap), give it the scan file.
- CVEs: you look them up, paste the data into a `cve-researcher` task (it has no web).
- PoC: `exploit-builder` (builder) -> `security-reviewer` (needs `--after <builder run id>`) -> YOUR review of the
  code -> only then the executor runs it. Risk = high.
- On `ask` from the executor: answer, or ask the user to widen SCOPE.md. Never let it spin.
- `exec:` in the summary: off-allowlist (exit 4), over budget or loop = change tack, don't re-dispatch.

## After
- One note per confirmed finding in `engagements/<name>/findings/`; loot in `loot/`; both stay local.
- `report-scribe` writes `engagements/<name>/report/`. A reusable, non-sensitive lesson about the setup -> `agent/notes/`.
- A new host found on the way is NOT in scope: tell the user, let them add it to SCOPE.md, then continue.
