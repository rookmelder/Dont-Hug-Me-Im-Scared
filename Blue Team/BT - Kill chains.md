---
tags: [blue-team, framework, methodology]
tools: []
ports: []
os: []
phase: []
---
# BT - Kill chains

**TL;DR:** Models that break an attack into ordered stages. **Cyber Kill Chain** = 7 linear stages (defense idea: break any one link and the attack fails). **Unified Kill Chain** = 18 phases that fix the CKC's gaps (no internal movement, perimeter-focused) by merging it with MITRE ATT&CK, grouped **In → Through → Out**.

from: TryHackMe (Cyber Kill Chain, Unified Kill Chain) — verified vs Lockheed Martin / unifiedkillchain.com

## Cyber Kill Chain (Lockheed Martin, 2011)

1. **Reconnaissance** — research target (emails, names, exposed systems).
2. **Weaponization** — pair a payload with an exploit/deliverable (e.g. macro doc).
3. **Delivery** — get it to the target (email, USB, web).
4. **Exploitation** — code runs, vuln triggered.
5. **Installation** — malware/backdoor planted for a foothold.
6. **Command & Control (C2)** — compromised host beacons out; attacker gains remote control.
7. **Actions on Objectives** — the actual goal: data theft, ransomware, sabotage, lateral movement.

Weakness: it's perimeter-centric and ends at "objectives" — it doesn't model what happens *inside* the network (lateral movement, privesc). It's a concept, not a strict sequence; stages get skipped/combined.

## Unified Kill Chain (Paul Pols, Fox-IT / Leiden, 2017)

18 phases across three macro-phases. Phases recur per compromised system (chained attacks).

- **In** (get a foothold): Reconnaissance, Weaponization, Delivery, Social Engineering, Exploitation, Persistence, Defense Evasion, Command & Control.
- **Through** (propagate inside): Pivoting, Discovery, Privilege Escalation, Execution, Credential Access, Lateral Movement.
- **Out** (act on target): Collection, Exfiltration, Impact, Objectives.
  - *Collection* — gather target data before exfil. *Exfiltration* — remove it. *Impact* — manipulate/interrupt/destroy (ransomware, wipe, deface, DoS). *Objectives* — the socio-technical end goal.

(Exact grouping varies by framework version — check unifiedkillchain.com if precise placement matters.)

## Why an attacker cares

These map 1:1 to the vault's `phase:` labels and tell you which defender detections fire at each step — see [[Methodology]].

## Related

- [[BT - SOC]]
- [[Methodology]]
