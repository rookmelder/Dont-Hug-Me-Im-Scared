---
tags: [recon, scanning]
tools: [wireshark]
ports: []
os: [linux, windows, macos]
phase: [recon, enum]
familiarity: reference
---
# Tool - Wireshark

**TL;DR:** Packet capture and analysis; the pcap is the evidence of what a scan did.

**My take:** Start capturing before the first scan. Filters are in [[Recon - Wireshark scan filters]].

from: SB - Active RECON (course chapter)

**Get it:** https://www.wireshark.org

## Install

```bash
sudo apt install wireshark
```

## Commands we use

```bash
wireshark -i <IFACE> -k   # start capturing straight away
```

## Gotchas

- Follow > TCP Stream shows a banner as the tool received it.
- Add `ip.ttl` as a column for OS clues.

## Related

- [[Recon]]
- [[Tools]]
