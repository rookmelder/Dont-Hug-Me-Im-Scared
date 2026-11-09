---
tags: [recon, scanning]
tools: [fping]
ports: []
os: [linux]
phase: [recon, enum]
familiarity: reference
---
# Tool - fping

**TL;DR:** Round-robin ping of many hosts or a whole range.

**My take:** Much faster than looping ping over a range.

from: SB - Active RECON (course chapter)

**Get it:** https://fping.org

## Install

```bash
sudo apt install fping
```

## Commands we use

```bash
fping -a -r 0 -g <CIDR>     # -a alive only, -r retries, -g generate range
```

## Gotchas

- No reply can mean filtered rather than down.

## Related

- [[Recon]]
- [[Tools]]
