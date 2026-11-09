---
tags: [enum, vuln-scanning]
tools: [legion]
ports: []
os: [linux]
phase: [enum]
familiarity: reference
---
# Tool - Legion

**TL;DR:** GUI that runs scans and enumeration tools and collects all output in one place.

**My take:** Point-and-click wrapper; the separate tools remain the default. Has MCP server support.

from: SB - Vulnerability scanning (course chapter)

**Get it:** https://www.kali.org/tools/legion/ (https://github.com/Hackman238/legion, demo: https://youtu.be/5lN2HN1OtqM)

## Install

```bash
sudo apt install legion
```

## Commands we use

```bash
sudo legion
```

## Gotchas

- Screenshot problems: see the Screenshot issues section of the GitHub README.
- MCP integration lets an AI drive tools, so keep it strictly inside scope.

## Related

- [[Recon - Vulnerability scanning overview]]
- [[Tools]]
