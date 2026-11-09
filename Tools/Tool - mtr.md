---
tags: [recon, network]
tools: [mtr, traceroute, tracert]
ports: []
os: [linux, windows]
phase: [recon]
familiarity: reference
---
# Tool - mtr

**TL;DR:** Live traceroute with per-hop loss and latency. On Windows the equivalent is `tracert`.

**My take:** Default for looking at a path on Linux. Interpretation is in [[Recon - Tracing the path and ASNs]].

from: Tracing the path (course chapter)

**Get it:** https://github.com/traviscross/mtr (Windows: `tracert` is built in)

## Install

```bash
sudo apt install mtr-tiny
```

## Commands we use

```bash
mtr <HOST>
tracert -d <HOST>     # Windows; -d skips reverse DNS
```

## Gotchas

- Each hop is found by raising the TTL by one and reading the ICMP "time exceeded" reply.
- `tracert` uses ICMP. Linux `traceroute` uses UDP by default, so results can differ through firewalls.
- Silent hops are often just routers that don't reply, not a break in the path.

## Related

- [[Recon]]
- [[Tools]]
