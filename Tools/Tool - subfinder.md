---
tags: [recon, osint]
tools: [subfinder]
ports: []
os: [linux]
phase: [recon]
familiarity: reference
---
# Tool - subfinder

**TL;DR:** Passive subdomain enumeration across many sources.

**My take:** Automates what a manual crt.sh query does, across more sources.

from: SE - OSINT (course chapter)

**Get it:** https://github.com/projectdiscovery/subfinder

## Install

```bash
sudo apt install subfinder
```

## Commands we use

```bash
subfinder -d <DOMAIN> -silent
```

## Gotchas

- Compare with crt.sh output; see [[Recon - OSINT domain footprint]].

## Related

- [[Recon]]
- [[Tools]]
