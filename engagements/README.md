# Engagements — per-project data (kept OUT of git)

This folder holds the real data for each testing engagement: scan output, loot, findings,
notes and the write-up. **It never goes to GitHub.** Only this `README.md` and the
`_TEMPLATE/` skeleton are tracked; every actual engagement folder is git-ignored
(see `.gitignore`). This repo is public — engagement data must stay on the VM.

## How it fits the framework

- `knowledge/` (in git) = the reusable **template** notes and the map. Keep it generic.
- `engagements/<name>/` (ignored) = the **real** data for one engagement at a time.
- `.worker/` (ignored) = scratch/logs from `delegate.py` runs.

So: curated, shareable patterns live in `knowledge/`; everything sensitive to a target
lives here under `engagements/<name>/` and stays local.

## Start a new engagement

```bash
cp -r engagements/_TEMPLATE engagements/<name>
```

Use a short, clear name per project, e.g. `htb-blue`, `acme-webapp`, `lab-proxmox`.

## Layout of each engagement

| Folder | What goes in it |
|---|---|
| `scans/`   | Raw tool output (nmap, nuclei, gobuster…). Big and noisy — summarise elsewhere. |
| `findings/`| One short note per confirmed finding (host, port, service, evidence). |
| `loot/`    | Creds, hashes, files pulled from in-scope targets. Stays local, in-report only. |
| `report/`  | The engagement write-up the Lead/report-scribe produces. |
| `notes/`   | Working notes, decisions, next steps for this engagement. |

## Rules

- **Nothing here is committed.** If `git status` ever shows an engagement file, stop —
  the ignore rule is wrong; fix it before pushing.
- One engagement per folder. Don't mix targets.
- Raw scan output goes to `scans/`; the `recon-analyst` worker summarises it into
  `findings/` before the Lead reads it.
- Keep `SCOPE.md` (repo root) authoritative — only touch targets listed there.
