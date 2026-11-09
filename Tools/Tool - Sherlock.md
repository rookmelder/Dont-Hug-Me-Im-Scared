---
tags: [recon, osint]
tools: [sherlock]
ports: []
os: [linux]
phase: [recon]
familiarity: reference
---
# Tool - Sherlock

**TL;DR:** Checks hundreds of sites for a username.

**My take:** Quick existence check; use [[Tool - Maigret]] when profile details matter.

from: SE - OSINT (course chapter)

**Get it:** https://github.com/sherlock-project/sherlock

## Install

```bash
sudo apt install sherlock
```

## Commands we use

```bash
sherlock <USERNAME>
```

## Gotchas

- A hit is a lead, not a match. Corroborate with photo, location, writing style or links between profiles.

## Related

- [[Recon]]
- [[Tools]]
