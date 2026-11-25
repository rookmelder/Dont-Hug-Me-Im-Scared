# SCOPE — authorisation and targets

**Every run reads this file. If a target is not listed below, it is OUT OF SCOPE. No exceptions.**

**Status:** NOT AUTHORISED YET — fill this in before any tool is run. While it says this, the Lead runs nothing
and dispatches no executor task.

## Authorisation
- I confirm I own these targets, or have **written permission** to test them: **(yes / no)** — `no`
- Authorised by: `<name / platform, e.g. "my homelab" / "TryHackMe" / "HTB">`
- Engagement window: `<start>` to `<end>` (nothing before or after)
- Evidence of permission: `<link / file / "I own the lab">`

## In scope (ONLY these)
List exact hosts, IP ranges and URLs. Nothing outside this list may be touched.
- `<e.g. 10.10.10.0/24  — my Proxmox lab>`
- `<e.g. 10.10.11.42    — HTB box "name" (only while the box is active on my account)>`
- `<e.g. metasploitable.lan>`

## Out of scope (hard rules)
- Everything not listed under **In scope** above, including the internet at large and any shared infrastructure.
- No pivoting to a host you discover but that is not listed here — stop and ask the Lead to add it to scope first.
- No denial-of-service, no destruction of data, no ransomware/wiper behaviour, no persistence/backdoors.
- No exfiltration of real data off any target. Loot stays in the report for the Lead.
- No action against third-party services the target talks to (upstream DNS, cloud APIs, other people's boxes).

## Rules of engagement
- Read-only enumeration first. Anything that exploits, writes or could disrupt a target waits for the Lead's OK.
- VPN / lab only: the HexStrike server and the workers run on the isolated VM; nothing leaves it.
- Stop immediately and tell the Lead if a target looks like production, like someone else's system, or out of the window.

<!-- The Lead (CLAUDE.md) and the executor base (agent/bases/executor.md) both require that work stays inside this
     file. Keep it current; when scope changes, change it here first, then run. -->
