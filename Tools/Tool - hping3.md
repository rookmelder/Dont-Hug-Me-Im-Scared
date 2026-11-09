---
tags: [network, dos, scanning]
tools: [hping3]
ports: []
os: [linux]
phase: [recon, exfil]
familiarity: reference
---
# Tool - hping3

**TL;DR:** Command-line TCP/IP packet crafter. Builds custom packets with any flags, size and (spoofed) source — used for firewall/rule testing, odd-flag probing, and lab DoS demonstrations.

**My take:** Reach for it when nmap can't shape the packet you need, or to reproduce a protocol attack in a lab. Flooding or spoofing is **lab-only or explicitly contracted** — it's disruptive and spoofed traffic reaches real networks.

from: SB - (D)DoS attacks (course chapter)

**Get it:** https://github.com/antirez/hping (in Kali)

## Install

```bash
sudo apt install hping3
```

## Commands we use

```bash
# single crafted SYN to a port (read the flags in the reply)
sudo hping3 -S -p <PORT> <TARGET>

# -S SYN flag, -p port, -a spoof source, -c count, -d data size,
# -w window, --flood send as fast as possible, --rand-source random spoofed src
```

Lab demonstrations against **your own isolated target only** (these are the course's examples; they disrupt the target):

```bash
# SYN flood (lab)
sudo hping3 -c 15000 -d 120 -S -w 64 -p 80 --flood --rand-source <LAB_TARGET>

# LAND (source = destination; old-stack demo)
sudo hping3 -S -p <PORT> <LAB_TARGET> -a <LAB_TARGET>
```

## Gotchas

- Raw packets need root.
- `-a` / `--rand-source` spoof the source, so replies never come back to you — you observe the effect on the target, not responses.
- Never point `--flood` or spoofing at anything you don't own or aren't contracted to test; DoS is out of scope in most audits.

## Related

- [[Network - DoS and DDoS]]
- [[Tools]]
