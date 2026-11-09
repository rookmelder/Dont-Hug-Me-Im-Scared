---
tags: [recon, scanning]
tools: [nmap]
ports: []
os: [linux, windows, macos]
phase: [recon, enum]
familiarity: go-to
---
# Tool - nmap

**TL;DR:** Host discovery, port scans, version detection and OS fingerprinting.

**My take:** Default scanner. Work the funnel: live hosts, then ports, then versions, then OS. See [[Recon - Port scanning TCP and UDP]].

from: SB - Active RECON (course chapter)

**Get it:** https://nmap.org (preinstalled on Kali; cheat sheet: https://hackertarget.com/nmap-cheatsheet-a-quick-reference-guide/)

## Install

```bash
sudo apt install nmap
```

## Commands we use

```bash
nmap -sn <SUBNET>                     # host discovery, no port scan
sudo nmap -sn -PR <SUBNET>            # ARP discovery on the local subnet
nmap -sn -PE <SUBNET>                 # force ICMP echo
sudo nmap -sS -p 21,22,80,445 <IP>    # SYN scan (root)
nmap -sT <IP>                         # connect scan (no root)
sudo nmap -sN <IP>; sudo nmap -sF <IP>; sudo nmap -sX <IP>   # NULL, FIN, Xmas
sudo nmap -sU -p 53,111,137,161 <IP>  # UDP, keep the list short
nmap -sV <IP>                         # service and version
sudo nmap -O <IP>                     # OS guess (root)
nmap -6 -sV <IPV6>                    # IPv6 target
nmap -6 -iL <FILE>                    # IPv6 target list
```

## Gotchas

- On a local subnet as root, `-sn` silently uses ARP. Add `-PE` to see ICMP.
- NULL, FIN and Xmas are unreliable against Windows, which sends RST regardless.
- Use `-T2` or `-T3` on fragile or production networks; printers, OT and legacy devices can hang under aggressive scans.

## Related

- [[Recon]]
- [[Tools]]
