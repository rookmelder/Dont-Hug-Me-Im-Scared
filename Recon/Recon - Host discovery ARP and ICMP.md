---
tags: [recon, scanning]
tools: [arp-scan, nmap, fping, ping]
ports: []
os: []
phase: [recon, enum]
---
# Recon - Host discovery ARP and ICMP

**TL;DR:** Inside the subnet use ARP: hosts can't ignore it, even with ping blocked. Across routers use ICMP, but no reply only means down or filtered.

```bash
sudo arp-scan --interface=<IFACE> --localnet
sudo nmap -sn -PR <SUBNET>
fping -a -r 0 -g <CIDR>
nmap -sn -PE <SUBNET>
ping -bnc1 <BROADCAST>     # broadcast ping; many hosts ignore it
```

| Reply | Meaning |
|---|---|
| ARP opcode 2 | Sender IP and MAC are alive on this segment |
| ICMP type 0 | Echo reply: host alive |
| ICMP type 3 | Unreachable (code 1 host, code 3 port) |

Tools: [[Tool - arp-scan]], [[Tool - fping]], [[Tool - nmap]]

from: SB - Active RECON (course chapter)

## Related

- [[Recon]]
- [[Method - 1 Recon]]
