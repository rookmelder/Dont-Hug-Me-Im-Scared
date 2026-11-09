---
tags: [recon, osint]
tools: [maltego]
ports: []
os: [linux, windows, macos]
phase: [recon]
familiarity: reference
---
# Tool - Maltego

**TL;DR:** Graphical link analysis: entities are nodes, transforms fetch related entities.

**My take:** For visualising pivots across many selectors, e.g. starting from an email or a domain.

from: SE - OSINT (course chapter)

**Get it:** https://www.maltego.com (docs: https://docs.maltego.com/support/home, videos: https://www.youtube.com/playlist?list=PLfRX-xJAc2yz6CjQVQuogJeCBoy8HbCOR)

## Install

```bash
sudo apt install maltego
```

## Commands we use

```bash
maltego   # register, then start a graph from a Domain or Email entity and run transforms
```

## Gotchas

- Needs registration. Licensing was restructured and the free tier now sits in the Basic plans; check https://www.maltego.com/pricing.

## Related

- [[Recon]]
- [[Tools]]
