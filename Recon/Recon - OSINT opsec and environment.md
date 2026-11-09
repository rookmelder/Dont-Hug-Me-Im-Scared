---
tags: [recon, osint]
tools: []
ports: []
os: []
phase: [recon]
---
# Recon - OSINT opsec and environment

**TL;DR:** Work from a clean VM with no personal accounts, look without touching, capture and hash as you go, and grade every finding by source and by information.

Environment: snapshot, separate browser profile, per-case folders `notes/ captures/ exports/ report/`. Revert after each case.

- Trace Labs OSINT VM: https://github.com/tracelabs/tlosint-vm (Debian 13 since 2026.05, no exploit or scan tooling, prebuilt OVA or install script)
- CSI Linux: https://csilinux.com (investigator distro, OSINT plus forensics)

Research accounts: only if the mandate allows; most platforms' ToS forbid them. View only, one per case, never linked to your real phone, email or network.

Evidence: full-page capture with URL and clock, timestamp with time zone, `sha256sum <CAPTURE>`, Save Page Now, and an activity log. Hunchly automates it: https://hunch.ly

4x4 grading: source A (reliable), B (mostly reliable), C (mostly unreliable), X (unknown). Information 1 (certain), 2 (known to source), 3 (not known to source, corroborated), 4 (not known, uncorroborated). Never present X4 as A1. Two sites copying one press release are one source.

AI: no case data in public services; verify every output against the original.

from: SE - OSINT (course chapter)

## Related

- [[Recon]]
- [[Method - 1 Recon]]
