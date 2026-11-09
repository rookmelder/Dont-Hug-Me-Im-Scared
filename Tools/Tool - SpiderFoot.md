---
tags: [recon, osint]
tools: [spiderfoot]
ports: []
os: [linux]
phase: [recon]
familiarity: reference
---
# Tool - SpiderFoot

**TL;DR:** Open-source OSINT automation: many modules against one target, results correlated.

**My take:** Use after the manual method. Automation doesn't replace judgement.

from: SE - OSINT (course chapter)

**Get it:** https://github.com/smicallef/spiderfoot (included in Kali)

## Install

```bash
sudo apt install spiderfoot
```

## Commands we use

```bash
spiderfoot -l 127.0.0.1:5001   # then browse to http://127.0.0.1:5001
```

## Gotchas

- Many modules need API keys (Shodan, Hunter, AlienVault OTX).
- Enable only passive modules unless active recon is in scope.

## Related

- [[Recon]]
- [[Tools]]
