---
tags: [blue-team, forensics, dfir]
tools: []
ports: []
os: [linux]
phase: []
---
# BT - Linux forensics

**TL;DR:** On a compromised Linux host, answer: who logged in, what did they run, and how do they persist. Logs + shell history + the persistence spots (cron, systemd, SSH keys). Collect **read-only**. Offensively, this is the list of what you leave behind.

from: TryHackMe Linux Server Forensics — verified vs DFIR references

## Logins

```bash
last -f /var/log/wtmp        # all logins (source for `last`)
lastb -f /var/log/btmp       # FAILED logins
lastlog                      # last login per user
```

## Authentication / sudo

- `/var/log/auth.log` (Debian/Ubuntu) or `/var/log/secure` (RHEL/CentOS) — logins, sudo use, SSH.
- `/var/log/syslog`, `/var/log/cron`, `/var/log/audit/audit.log` (auditd).

## What ran

- `~/.bash_history` (and root's), `.zsh_history`, `.python_history`. Missing/truncated history is itself a finding (attacker cleaned up).

## Persistence to check

- **Cron:** `/etc/crontab`, `/etc/cron.*`, per-user `crontab -l`, `/var/spool/cron/`.
- **systemd:** unit files in `/etc/systemd/system/`, `~/.config/systemd/user/` — odd ExecStart.
- **SSH:** each user's `~/.ssh/authorized_keys` (attacker-added keys).
- **Accounts:** new UID 0 entries in `/etc/passwd`, recent changes to `/etc/passwd`/`/etc/shadow`.
- **Startup/loader:** `/etc/rc.local`, `/etc/ld.so.preload`, `/etc/profile.d/`.
- **PAM:** diff `/etc/pam.d/` against a known-good baseline.

## Key point

Treat a cleared `.bash_history` or a `1102`-style "logs cleared" gap as evidence, not absence of evidence.

## Related

- [[BT - Hardening basics]], [[BT - Windows forensics]], [[BT - SIEM]]
