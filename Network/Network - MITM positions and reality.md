---
tags: [network, mitm]
tools: [bettercap, mitmproxy, burp]
ports: []
os: [linux, windows]
phase: [credential-access, initial-access]
---
# Network - MITM positions and reality

**TL;DR:** A man-in-the-middle (modern name **Adversary-in-the-Middle, AiTM**, MITRE **T1557**) is a *position*, not a single trick. Any time a party decides "this is who I'm talking to" without cryptographic proof, that decision can be captured. Win the trust decision first; sniffing vs. modifying is just what you do after. In a TLS-everywhere world the position yields far less than the classic demos suggest.

from: SB - Man-in-the-Middle Security & Defense (course chapter)

## Terminology

MITM = PITM = MitM = **AiTM** (T1557) — same mechanic, different labels. SOC logs and SIEMs use **AiTM**. Variant: Adversary-in-the-Browser (AiTB), client-side malware that edits transactions inside the browser before TLS applies. The sub-techniques map the vault notes:

- **T1557.001** LLMNR/NBT-NS poisoning + SMB relay → [[AD - LLMNR and NBT-NS poisoning]]
- **T1557.002** ARP cache poisoning → [[Network - ARP cache poisoning]]
- **T1557.003** DHCP spoofing (and the IPv6/mitm6 cousin) → [[Network - Rogue DHCP DNS and IPv6 mitm6]]

## Passive vs. active

- **Passive** — you can only see the traffic (span port, shared medium). Read/analyse, nothing changed → hard to detect. Goal: credential/data harvesting, recon.
- **Active (true MITM)** — both parties route *through* you. Read **and** modify/inject/drop → leaves traces (duplicate MAC mappings, extra hops, timing, cert warnings). Goal: session hijack, downgrade, relay, injection.

Position precedes action. Every technique in this topic is a different way to win the position across a network layer.

## CIANA impact

Confidentiality (eavesdrop cleartext/tokens), Integrity (alter transit data, inject code/setpoints), Availability (drop/disrupt sessions), Non-repudiation (destroy the audit trail by acting as someone else), Authentication (the whole attack *is* identity spoofing — ARP/NDP spoof, rogue gateway, forged cert).

## What a middle position still yields in 2026

The classic demo (sniff logins, images, URLs) mostly **fails** now — the web is HTTPS + HSTS (preload lists make browsers refuse plain HTTP first). You see TLS: destinations and sizes, not contents. What's still useful:

- **Metadata** — who talks to whom, when, how much. Good for intel, rarely creds.
- **Whatever is still cleartext** — legacy internal services, plain DNS, misconfigured apps, and **OT protocols** (Modbus TCP, S7Comm, unencrypted RTSP) that have no auth of their own. On flat IT/OT segments a setpoint can in principle be altered → MITM there is a *safety* issue, not just confidentiality.
- **Downgrade / TLS-strip** — largely dead against HSTS-preloaded sites; situational now.
- **Authorised CA interception** — in a sanctioned test you install your own CA on the test endpoint and use an intercepting proxy (Burp, mitmproxy). This reads TLS because you own the endpoint and planted the trust — a testing technique, not a remote attack.

To demo cleartext honestly, use a deliberately-plain target: http://httpforever.com , http://www.stealmylogin.com .

## Related

- [[Network - ARP cache poisoning]]
- [[Network - Rogue DHCP DNS and IPv6 mitm6]]
- [[AD - LLMNR and NBT-NS poisoning]]
- [[Method - Legal and authorization (Belgium)]]
- [[Network]]
