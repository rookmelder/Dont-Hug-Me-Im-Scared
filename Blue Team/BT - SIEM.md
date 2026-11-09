---
tags: [blue-team, siem, logging]
tools: [siem]
ports: []
os: []
phase: []
---
# BT - SIEM

**TL;DR:** Security Information and Event Management: collects logs from many sources, puts them in one format, and runs correlation rules to raise alerts. The pipeline is **ingest → parse → normalize → correlate → alert**.

from: TryHackMe (Introduction to SIEM, SOC Level 1) — verified vs vendor SIEM references

## The pipeline

1. **Ingestion** — collect logs. Two broad source types:
   - *Host-centric:* Windows Event logs, Sysmon, auth logs, process/file/registry activity on an endpoint.
   - *Network-centric:* firewall, proxy, IDS/IPS, netflow, VPN, DNS.
2. **Parsing** — split a raw log line into fields.
3. **Normalization** — map those fields into one consistent schema, so "src IP" means the same thing whichever product logged it. Required before correlation.
4. **Correlation** — analyst-written logical rules across normalized events (e.g. *many failed logins then one success* = possible brute force). The correlation engine evaluates these in real time.
5. **Alerting / dashboards** — rule fires → alert into the Tier 1 queue; dashboards show live state.

## Use cases

A "use case" is the specific threat scenario a rule is built to catch. Best practice: define clear use cases, prioritise high-value log sources, normalize for correlation, and validate ingestion/parsing actually works.

## Offensive takeaway

This is what logs you. Failed-then-successful logins, new service installs, odd parent-child process trees (e.g. Office spawning PowerShell) and known-bad command lines are classic correlation rules. Blending into normal patterns beats volume.

## Related

- [[BT - SOC]]
- [[BT - Kill chains]]
