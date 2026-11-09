---
tags: [blue-team, soc]
tools: [siem, edr]
ports: []
os: []
phase: []
---
# BT - SOC

**TL;DR:** A Security Operations Center monitors, detects, investigates and responds to threats. Built on **people + process + technology**. Analysts are tiered 1→3 by depth; the "junior analyst" job is Tier 1 triage.

from: TryHackMe (SOC Fundamentals, Junior Analyst Intro) — verified vs common SOC references

## People / process / technology

- **People** — tiered analysts, incident responders, threat hunters, SOC manager.
- **Process** — the repeatable playbooks. Without process, every alert becomes a one-off investigation.
- **Technology** — SIEM, EDR, SOAR, case management, threat-intel platforms.

## Analyst tiers

- **Tier 1 — Triage (the junior analyst):** front line. Watch the SIEM/EDR alert queue, do initial analysis, filter false positives, escalate real incidents. Increasingly assisted/replaced by SOAR automation.
- **Tier 2 — Investigation:** deeper analysis, confirm/refute T1 verdicts, correlate logs, analyse IOCs, contain confirmed threats.
- **Tier 3 — Hunting & engineering:** threat hunting, malware/memory/forensic analysis, detection engineering (writing SIEM/IDS/EDR rules), improving SOC processes.

(Tier boundaries vary by org — this is the common model, not a fixed standard.)

## Offensive takeaway

Tier 1 drowns in alerts and filters false positives — noisy, "textbook" attacks get triaged fast; low-and-slow blends in. What you do loudly (scans, failed logins, known-bad tooling) is exactly what their correlation rules key on. See [[BT - SIEM]].

## Related

- [[BT - SIEM]]
- [[BT - Kill chains]]
