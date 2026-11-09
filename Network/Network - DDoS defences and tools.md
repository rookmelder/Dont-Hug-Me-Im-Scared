---
tags: [network, ddos, defense]
tools: []
ports: []
os: []
phase: [exfil]
---
# Network - DDoS defences and tools

**TL;DR:** You rarely out-muscle a volumetric attack on your own link — you absorb it upstream (CDN/scrubbing) and harden the host against the cheap protocol and app-layer attacks. For an audit, you measure readiness rather than launch an attack.

from: SB - (D)DoS attacks (course chapter)

## Defences, roughly in order

1. **Upstream absorption** — a CDN / reverse proxy (Cloudflare, Akamai) sits in front, caches, and soaks volume far bigger than your own pipe.
2. **Edge anti-spoofing** — BCP 38 / uRPF so spoofed source IPs can't leave your network; this is what makes reflection/amplification possible when everyone skips it.
3. **Don't expose amplifiers** — no open NTP `monlist`, open DNS resolvers, CharGEN, SSDP to the Internet.
4. **Host/stack hardening** — SYN cookies, connection and header timeouts, per-IP limits, rate limiting, an event-driven front end for slow-and-low attacks.
5. **Dedicated appliances** at the perimeter for large or always-on targets (below).
6. **A plan** — upstream/ISP contacts and a runbook before it happens; a score to track readiness.

## Readiness and audit

- **DDoS Resiliency Score (DRS)** — quantifies which attack types you can withstand before outage: https://www.ddosresiliencyscore.org/
- Stress-test / DDoS-audit providers (contracted, authorised testing only): Red Button https://www.red-button.net/, zeroBS https://zero.bs/, Radware Red Teaming https://www.radware.com/lp/redteamingwebinarseries/
- Quick single-IP check (defender): https://www.techrepublic.com/article/how-to-quickly-check-to-see-if-your-linux-server-is-under-a-ddos-attack-from-a-single-ip-address/

## Mitigation products (reference)

- CDN / cloud: Cloudflare https://www.cloudflare.com/ddos/, Akamai
- Appliances: Radware DefensePro https://www.radware.com/products/defensepro/, NETSCOUT/Arbor https://www.netscout.com/arbor-ddos, Check Point DDoS Protector https://www.checkpoint.com/products/ddos-protector/

## Attack tools (reference only — know them to detect/defend)

These are the tools named in the course; listed so you can recognise their traffic and read incident write-ups. Point them only at systems you own or are contracted to stress-test.

- **hping3** — packet crafting / testing; the genuinely reusable one. See [[Tool - hping3]].
- **LOIC / HOIC** — volunteer "ion cannon" flooders (TCP/UDP, and HTTP for HOIC); historically used by Anonymous. Easy to detect (fixed payloads).
- **Slowloris** (https://github.com/gkbrk/slowloris) / **R.U.D.Y** — low-and-slow thread exhaustion.
- **UDP Unicorn** — Windows UDP flooder.
- **Smurf6** — IPv6 multicast smurf.
- **Blacknurse** (http://blacknurse.dk/) — low-bandwidth ICMP 3/3 against firewalls.

## Watch / context

- Live maps: https://www.netscout.com/ddos-attack-map, https://horizon.netscout.com/, https://digitalattackmap.com/
- Internet shutdown monitoring: https://netblocks.org/
- **Ransom DDoS (RDDoS)** — extortion ("pay or we flood you"). Advice is not to pay: no guarantee, and it invites repeat demands. Distinct from ransomware (no network intrusion, just disruption); now seen as a leg of triple extortion (encryption + leak + DDoS).
- **Booter / stresser ("DDoS-for-hire")** and dark-web marketplaces exist and are cheap — and using them is a crime. The course links specific services; they're deliberately not copied here as they have no defensive use. Background: https://socradar.io/dark-web-stories-ddos-as-a-service/
- Mirai showed IoT botnets as a volumetric source; appliances now advertise Mirai/Pulse/Burst mitigation.

## Related

- [[Network]]
- [[Network - DoS and DDoS]]
