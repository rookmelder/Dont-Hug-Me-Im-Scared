---
tags: [recon, osint]
tools: [theharvester]
ports: []
os: [linux]
phase: [recon]
familiarity: reference
---
# Tool - theHarvester

**TL;DR:** Collects emails, names, subdomains and hosts for a domain from public sources.

**My take:** First pass for domain to people and hosts; broader than [[Tool - emailharvester]].

from: SE - OSINT (course chapter)

**Get it:** https://github.com/laramies/theHarvester (in Kali and the Trace Labs VM)

## Install

```bash
sudo apt install theharvester
```

## Commands we use

```bash
theHarvester -h   # list the sources this version supports
theHarvester -d <DOMAIN> -b crtsh,duckduckgo,hackertarget
```

## Gotchas

- Supported sources change between versions (LinkedIn is gone), so check `-h` first.
- Many sources need a key in `api-keys.yaml`.

## Related

- [[Recon]]
- [[Tools]]
