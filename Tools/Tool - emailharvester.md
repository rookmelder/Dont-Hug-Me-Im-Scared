---
tags: [social-engineering, recon, osint]
tools: [emailharvester]
ports: []
os: [linux]
phase: [recon]
familiarity: reference
---
# Tool - emailharvester

**TL;DR:** Collects email addresses for a domain from public sources — footprinting input for phishing/OSINT.

**My take:** Quick domain → email list. Can be slow (grab a coffee). For broader OSINT also consider theHarvester.

## Install

```bash
sudo apt update && sudo apt install emailharvester
```

## Commands we use

```bash
emailharvester -h
emailharvester -d <DOMAIN>
```

## Related

- [[SE - Phishing variants]]
- [[Recon]]
- [[Tools]]
