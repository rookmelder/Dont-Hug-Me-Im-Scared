---
tags: [blue-team, forensics, dfir]
tools: []
ports: []
os: [windows]
phase: []
---
# BT - Windows forensics

**TL;DR:** Windows leaves artifacts proving a file *existed* vs that it *ran* — don't confuse the two. Registry hives hold config + user activity; a separate set of artifacts covers program execution. Offensively, this is the list of things that outlive your session on disk.

from: TryHackMe Windows Forensics 1 — verified vs Microsoft IR / DFIR references

## Registry hives (on disk)

Stored in `C:\Windows\System32\config\` (system) and each user's profile; loaded to memory at runtime, flushed on shutdown.

- **SAM** — local account names + password hashes.
- **SYSTEM** — services, drivers, mounted devices, current control set.
- **SOFTWARE** — installed software, OS version, autostart (`Run` keys).
- **SECURITY** — policy, cached domain creds (LSA secrets).
- **NTUSER.DAT** (per user, in profile) — that user's activity: UserAssist, RecentDocs, typed paths, MRU.

## Evidence of execution (ran vs existed)

- **Prefetch** (`C:\Windows\Prefetch\*.pf`) — run count + last-run times (last 8). Strong "it ran" evidence; created even on crash. Parse with PECmd.
- **Shimcache / AppCompatCache** (SYSTEM hive) — proves a file **existed** (survives deletion); not reliable for execution time.
- **Amcache.hve** (`C:\Windows\AppCompat\Programs\`) — presence + SHA-1 of binaries; "evidence of presence", not proof of execution.
- **BAM/DAM** (SYSTEM hive) — programs run per user, with timestamps.
- **SRUM** — app resource usage over time.
- **UserAssist** (NTUSER.DAT) — GUI programs the user launched, run count + focus time.

## Key point

Shimcache/Amcache = existed. Prefetch/BAM/UserAssist = ran. Correlate before concluding.

## Related

- [[BT - Investigating Windows]], [[BT - SIEM]]
