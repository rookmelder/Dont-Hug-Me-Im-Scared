---
tags: [network, mitm]
tools: [bettercap]
ports: []
os: [linux]
phase: [credential-access, lateral]
familiarity: learning
---
# Tool - bettercap

**TL;DR:** All-in-one MITM framework (Go). ARP/DNS/DHCPv6/NDP spoofing, a scriptable sniffer, packet/TCP/HTTP(S) proxies, plus Wi-Fi/BLE/HID attacks. The modern successor to the legacy **Ettercap** and **Yersinia**.

**My take:** Reach for this instead of juggling `arpspoof` + `dsniff` — it does spoof + sniff + proxy in one interactive session. Still `learning`; see [[Network - ARP cache poisoning]] and [[Network - Rogue DHCP DNS and IPv6 mitm6]] for where it fits.

from: SB - Man-in-the-Middle Security & Defense (course chapter)

**Get it:** https://www.bettercap.org (docs), https://www.bettercap.org/installation/ , releases: https://github.com/bettercap/bettercap/releases

Legacy predecessors (reference only): Ettercap https://www.ettercap-project.org/ , Yersinia https://www.kali.org/tools/yersinia/ (L2 protocol attack framework).

## Install

```bash
sudo apt install bettercap          # Kali
# or build/download a release from the github releases page above
```

## Commands we use (interactive session)

```text
net.probe on                        # discover hosts on the segment
net.show                            # list them

set arp.spoof.targets <TARGET_IP>   # ARP MITM
arp.spoof on

net.sniff on                        # capture; net.sniff off to stop

set dns.spoof.domains <DOMAINS>     # DNS spoofing
dns.spoof on

net.probe off
```

## Gotchas

- Enable IP forwarding or you blackhole the victim — bettercap usually handles this, but verify `net.ipv4.ip_forward=1`.
- Only ever spoof scoped targets; unconstrained spoofing on a live net is disruptive and out of scope — see [[Method - Legal and authorization (Belgium)]].
- Against TLS/HSTS sites you get metadata, not contents — see [[Network - MITM positions and reality]].

## Related

- [[Network - ARP cache poisoning]]
- [[Tools]]
