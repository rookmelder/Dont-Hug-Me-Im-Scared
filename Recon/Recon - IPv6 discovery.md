---
tags: [recon, scanning]
tools: [ping, nmap, masscan]
ports: []
os: []
phase: [recon, enum]
---
# Recon - IPv6 discovery

**TL;DR:** On the local link, ping all-hosts multicast. Remotely a /64 can't be swept, so build a target list first and scan only that.

```bash
ping6 -nc2 ff02::1%<IFACE>     # all hosts on the link; -n skips reverse DNS
nmap -6 -sn <IPV6_TARGETS>
nmap -6 -iL <FILE>
```

Building a remote target list:
- AAAA records (`dig AAAA <HOST>`), certificate transparency logs, and prefixes from RIPE, ARIN or BGP data.
- Admin patterns: `::1`, `::2`, `::10`, embedded IPv4 (`::192:168:1:50`), service numbers (`::80`, `::53`), hex words (`::cafe`).
- EUI-64: addresses containing `ff:fe` derive from the MAC, so a known vendor OUI shrinks the search.
- Seen in the wild: scanners joining the NTP pool to harvest client addresses: https://isc.sans.edu/forums/diary/Targeted+IPv6+Scans+Using+poolntporg/20681/

from: SB - Active RECON (course chapter)

## Related

- [[Recon]]
- [[Method - 1 Recon]]
