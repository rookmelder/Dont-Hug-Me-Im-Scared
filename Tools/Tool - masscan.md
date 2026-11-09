---
tags: [recon, scanning]
tools: [masscan]
ports: []
os: [linux]
phase: [recon, enum]
familiarity: reference
---
# Tool - masscan

**TL;DR:** Very high-rate port scanner for large ranges.

**My take:** Only for big ranges in scope; nmap stays the default.

from: SB - Active RECON (course chapter)

**Get it:** https://github.com/robertdavidgraham/masscan

## Install

```bash
sudo apt install masscan
```

## Commands we use

```bash
masscan <CIDR> -p80,443 --rate 1000
```

## Gotchas

- A high `--rate` can crash routers or firewalls and trips IDS/IPS.
- The source chapter shows `--ipv6`; check `masscan --help` on your version, as IPv6 targets are normally just given directly.
- Even at high rates a full /64 is not scannable: build a target list first, see [[Recon - IPv6 discovery]].

## Related

- [[Recon]]
- [[Tools]]
