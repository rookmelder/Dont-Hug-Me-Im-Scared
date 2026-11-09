---
tags: [recon, scanning]
tools: [wireshark]
ports: []
os: []
phase: [recon, enum]
---
# Recon - Wireshark scan filters

**TL;DR:** Verify a scanner against the wire. Each scan has a decisive packet and a recognisable pattern. Tool: [[Tool - Wireshark]].

| Scan | Filter | ATT&CK |
|---|---|---|
| ARP sweep | `arp.opcode==1`, `arp.dst.hw_mac==00:00:00:00:00:00` | T1018 |
| Live via ARP | `arp.opcode==2` | T1018 |
| Ping sweep | `icmp.type==8` | T1018 / T1595.001 |
| Live via ICMP | `icmp.type==0` | T1018 |
| IPv6 | `icmpv6.type==128`; NDP `135` / `136` | T1018 |
| Raw SYN scan | `tcp.flags.syn==1 && tcp.flags.ack==0 && tcp.window_size<=1024` | T1046 |
| Connect scan | same with `tcp.window_size>1024` | T1046 |
| Open port | `tcp.flags.syn==1 && tcp.flags.ack==1` | T1046 |
| Closed port | `tcp.flags.reset==1` | T1046 |
| NULL / FIN / Xmas | `tcp.flags==0x000` / `0x001` / `0x029` | T1046 |
| UDP closed port | `icmp.type==3 && icmp.code==3` | T1046 |
| Banner | `ftp`, `ssh`, `http.response`, then Follow TCP Stream | T1046 |
| OS clues | `ip.ttl` as a column | T1082 |

Spotting scans: Statistics > Endpoints or Conversations shows one source against many hosts or ports. NULL, FIN and Xmas packets are abnormal on their own.

ATT&CK depends on position: from outside it's Reconnaissance (TA0043), from inside it's Discovery (TA0007). An internal scan means someone is already in.

from: SB - Active RECON (course chapter)

## Related

- [[Recon]]
- [[Method - 1 Recon]]
