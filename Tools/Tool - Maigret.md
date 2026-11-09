---
tags: [recon, osint]
tools: [maigret]
ports: []
os: [linux]
phase: [recon]
familiarity: reference
---
# Tool - Maigret

**TL;DR:** Username search across sites that also extracts profile information.

**My take:** Like [[Tool - Sherlock]] with more detail per hit.

from: SE - OSINT (course chapter)

**Get it:** https://github.com/soxoj/maigret

## Install

```bash
pipx install maigret
```

## Commands we use

```bash
maigret <USERNAME>
```

## Gotchas

- Same rule as Sherlock: corroborate every hit.

## Related

- [[Recon]]
- [[Tools]]
