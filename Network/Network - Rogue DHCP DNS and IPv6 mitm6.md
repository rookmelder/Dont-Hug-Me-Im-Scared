---
tags: [network, mitm, dhcp, dns, ipv6]
tools: [mitm6, bettercap, nmap, wireshark]
ports: [53, 546, 547]
os: [linux, windows]
phase: [credential-access, lateral]
---
# Network - Rogue DHCP, DNS and IPv6 (mitm6)

**TL;DR:** ARP decides "which MAC"; these attacks win the layer above — "which IP / which settings". A rogue **DHCP** server (T1557.003) hands out a gateway/DNS you control; **DNS spoofing** answers queries with false IPs; and the quietest of all, **IPv6/mitm6**, exploits the fact that Windows prefers IPv6 and begs for IPv6 config even on "IPv4-only" nets — answer it and you become its DNS server without ever touching ARP.

from: SB - Man-in-the-Middle Security & Defense (course chapter)

## The three naming/config decisions

- **Rogue DHCP** — answer DHCP faster than the real server, hand the victim your gateway/DNS. A middle position with no ARP. ([T1557.003](https://attack.mitre.org/techniques/T1557/003/))
- **DNS spoofing / cache poisoning** — supply a false IP for a name so the victim "correctly" connects to the wrong host. On a shared segment, usually paired with one of the positions above.
- **IPv6 — the forgotten layer** — modern Windows enables IPv6 by default and probes for routers/DNS (ICMPv6 Neighbor Solicitation, DHCPv6 Solicit) regardless of whether IPv6 was ever deployed. NDP is the IPv6 ARP and is **unauthenticated** (the secure spec, SEND/RFC 3971, is virtually never deployed). Because IPv6 is usually unmonitored, it's an ideal vector on flat nets.

## mitm6 mechanics

Because nothing legitimately answers IPv6, **mitm6** replies to the DHCPv6 solicits: it assigns the victim a link-local IPv6 address and declares the attacker as the primary IPv6 **DNS server**. Windows prefers IPv6 DNS, so the victim then queries the attacker for *all* names (A and AAAA) — bypassing IPv4 controls entirely. Classic follow-on: spoof WPAD → capture/relay auth (ties into [[AD - LLMNR and NBT-NS poisoning]]). See [[Tool - mitm6]].

## Non-destructive auditing

- **Rogue DHCP:** confirm DHCP Snooping is on and access ports are *untrusted* / uplinks *trusted*; map responders with `nmap --script broadcast-dhcp-discover` (and `dhcp6-discover` for v6) to see if rogue offers are filtered.
- **DNS:** passively watch how clients resolve internal names (A/AAAA); in an isolated lab, have an unauthorized node answer and see if the victim blindly accepts it before the real server replies.
- **IPv6:** on a lab range, open Wireshark and watch the Windows host emit ICMPv6 NS and DHCPv6 Solicit unprompted — proof that "IPv6 is on and unwatched".

## Defend

- **First-Hop Security:** DHCP Snooping + DAI globally; for IPv6, **RA Guard** and **DHCPv6 Guard** on access switches to block rogue router advertisements and config replies.
- **Disable unused IPv6** via GPO if it isn't used; otherwise deploy the IPv6 FHS above (don't just ignore it).
- Segment and monitor DNS so stray nodes can't win resolution on shared segments.

**SOC signs:** unexpected DHCP/DHCPv6 offers, a new IPv6 DNS server, WPAD lookups over IPv6. Detect with Suricata/Snort (FOX-IT published DHCPv6-advertise and WPAD-over-IPv6 sigs); prevent with DHCP-snooping trust ports. See [[Tool - mitm6]] for the signatures.

## Related

- [[Network - ARP cache poisoning]]
- [[Network - MITM positions and reality]]
- [[Tool - mitm6]]
- [[Recon - IPv6 discovery]]
- [[Network]]
