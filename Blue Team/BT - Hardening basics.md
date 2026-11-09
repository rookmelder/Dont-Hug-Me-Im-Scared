---
tags: [blue-team, hardening, defense]
tools: []
ports: []
os: [linux]
phase: []
---
# BT - Hardening basics

**TL;DR:** Shrink the attack surface: patch, remove what you don't need, enforce least privilege, and lock remote access. Offensively, this is the inverse of your privesc checklist — a hardened box closes the exact paths in [[Privesc - Linux sudo and SUID]] and [[Privesc - Linux cron and misc]].

from: TryHackMe Hardening Basics Part 1 & 2 — verified vs CIS-style baselines

## Core principles

- **Patch** — keep the kernel and packages current (`unattended-upgrades`); most exploits hit known CVEs.
- **Least privilege** — minimal sudo rules (no `NOPASSWD` on shell-escapable binaries), no shared root, remove users from unneeded groups (docker/lxd = root-equivalent).
- **Reduce surface** — disable/remove unused services and packages; close ports you don't serve.
- **File permissions** — no world-writable files/dirs, audit SUID/SGID, keep cron scripts and PATH dirs root-owned.

## Remote access (SSH)

```
PermitRootLogin no
PasswordAuthentication no        # keys only
AllowUsers <user>                # whitelist
Port <non-default optional>
```
Add **fail2ban** to throttle brute force.

## Firewall

```bash
ufw default deny incoming; ufw allow <service>; ufw enable
# or iptables / nftables equivalents
```

## Logging & monitoring

Enable **auditd**, ship logs off-host (feeds a [[BT - SIEM]]), and baseline configs so changes are detectable — see [[BT - Linux forensics]].

## Related

- [[BT - Linux forensics]], [[BT - SIEM]], [[Privesc]]
