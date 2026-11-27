# Engagements — per-project data (kept OUT of git)

This folder holds the real data for each testing engagement: scan output, loot, findings,
notes and the write-up. **It never goes to GitHub.** Only this `README.md` and the
`_TEMPLATE/` skeleton are tracked; every actual engagement folder is git-ignored
(see `.gitignore`). This repo is public — engagement data must stay on the VM.

## How it fits the framework

- `agent/notes/` (in git) = reusable, generic lessons about the setup.
- `engagements/<name>/` (ignored) = the **real** data for one engagement at a time.
- `.worker/` (ignored) = scratch/logs from `delegate.py` runs.

So: generic setup lessons live in `agent/notes/`; everything sensitive to a target
lives here under `engagements/<name>/` and stays local.

## Start a new engagement

```bash
cp -r engagements/_TEMPLATE engagements/<name>
```

Use a short, clear name per project, e.g. `htb-blue`, `acme-webapp`, `lab-proxmox`.

## Layout of each engagement

| File / folder | What goes in it |
|---|---|
| `GOAL.md`  | What you want tested this engagement (you write it). Filled from `_TEMPLATE`. |
| `SCOPE.md` | **Authorisation + the only allowed targets.** The Lead reads it before anything runs. |
| `scans/`   | Raw tool output (nmap, nuclei, gobuster…). Big and noisy — summarise elsewhere. |
| `findings/`| One short note per confirmed finding (host, port, service, evidence). |
| `loot/`    | Creds, hashes, files pulled from in-scope targets. Stays local, in-report only. |
| `report/`  | The engagement write-up the Lead/report-scribe produces. |
| `notes/`   | Working notes, decisions, next steps for this engagement. |

`PROJECT.md` is the one engagement file that does **not** live here: it stays at the repo root (the only place
`delegate.py` reads it), copied from `PROJECT.example.md`, and is git-ignored too. Keep it matched to the active
engagement.

## Rules

- **Nothing here is committed.** If `git status` ever shows an engagement file, stop —
  the ignore rule is wrong; fix it before pushing.
- One engagement per folder, one active at a time. Don't mix targets.
- Raw scan output goes to `scans/`; the `recon-analyst` worker summarises it into
  `findings/` before the Lead reads it.
- Keep this engagement's `SCOPE.md` authoritative — only touch targets listed there.
