---
tags: [recon, scanning]
tools: [nmap]
ports: []
os: []
phase: [recon, enum]
---
# Recon - Port scanning TCP and UDP

**TL;DR:** TCP state comes from the reply to a SYN. UDP is inverted: only a closed port answers clearly, so silence is ambiguous and scans are slow.

| Probe | Open | Closed | Filtered |
|---|---|---|---|
| TCP SYN | SYN/ACK | RST | nothing |
| NULL / FIN / Xmas | nothing | RST | nothing |
| UDP | nothing or service reply | ICMP 3/3 | nothing |

- `-sS` needs root, answers a SYN/ACK with RST and never completes the handshake.
- `-sT` needs no root, completes the handshake through the OS, and is slower and more visible.
- NULL, FIN and Xmas can slip past filters that only watch SYN; Windows answers RST regardless.
- UDP waits on a timeout per silent port, so a full range can take hours. Make port 53 answer for real to prove it open.

Commands: [[Tool - nmap]]

from: SB - Active RECON (course chapter)

## Related

- [[Recon]]
- [[Method - 1 Recon]]
