---
tags: [recon, scanning]
tools: [nc, nmap]
ports: []
os: []
phase: [recon, enum]
---
# Recon - Service and OS fingerprinting

**TL;DR:** Banners give service and version; TTL, window size and TCP options together suggest the OS. A single clue isn't proof.

```bash
nc <IP> <PORT>
nmap -sV <IP>
sudo nmap -O <IP>
```

| Clue | Linux | Windows |
|---|---|---|
| Initial TTL | 64 | 128 |
| TCP window | 5840 / 29200 (varies) | 8192 / 65535 (varies) |

- The TTL you see has been decremented per hop: 63 started at 64.
- Copyright years and strings in pages, JS libraries and firmware files can date the software when no banner exists.
- Recon stops at the version; checking it for vulnerabilities is the next phase.

from: SB - Active RECON (course chapter)

## Related

- [[Recon]]
- [[Method - 1 Recon]]
