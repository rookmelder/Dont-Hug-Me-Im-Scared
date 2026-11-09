---
tags: [recon, scanning]
tools: [arp-scan]
ports: []
os: [linux]
phase: [recon, enum]
familiarity: reference
---
# Tool - arp-scan

**TL;DR:** Fast ARP sweep of the local subnet, with MAC vendor lookup.

**My take:** Most reliable discovery inside a subnet: firewalled hosts still answer ARP.

from: SB - Active RECON (course chapter)

**Get it:** https://github.com/royhills/arp-scan

## Install

```bash
sudo apt install arp-scan
```

## Commands we use

```bash
ip a   # find the interface name
sudo arp-scan --interface=<IFACE> --localnet
```

## Gotchas

- Local segment only, because ARP isn't routed.
- The vendor can reveal a VM.

## Related

- [[Recon]]
- [[Tools]]
