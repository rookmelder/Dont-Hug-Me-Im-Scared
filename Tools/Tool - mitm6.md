---
tags: [network, mitm, ipv6]
tools: [mitm6]
ports: [53, 546, 547]
os: [linux]
phase: [credential-access, lateral]
familiarity: learning
---
# Tool - mitm6

**TL;DR:** Exploits Windows' default IPv6 behaviour: it replies to the victim's DHCPv6 solicits, hands out a link-local IPv6 address, and sets the attacker as the victim's primary **IPv6 DNS server**. Windows prefers IPv6 DNS, so it then sends all name queries (A and AAAA) to you — a middle position without touching ARP. Usual next step: spoof WPAD → relay auth (with ntlmrelayx).

**My take:** The quiet way onto a "IPv4-only" Windows network. Still `learning`. Mechanics and defences live in [[Network - Rogue DHCP DNS and IPv6 mitm6]].

from: SB - Man-in-the-Middle Security & Defense (course chapter)

**Get it:** https://github.com/dirkjanm/mitm6 , https://www.kali.org/tools/mitm6/

## Install

```bash
pipx install mitm6
```

## Usage

```bash
# -i interface; -d limits spoofing to a domain; -hw whitelists a single host (SAFETY)
sudo mitm6 -i <IFACE> -d <DOMAIN> -hw <SINGLE_TEST_HOST>
```

- **Phase 1 — DNS takeover:** mitm6 listens for Windows DHCPv6 solicits (every Windows since Vista asks regularly) and answers them.
- **Phase 2 — DNS spoofing:** victim now uses the attacker as DNS for both A and AAAA records.

Full write-ups: https://blog.fox-it.com/2018/01/11/mitm6-compromising-ipv4-networks-via-ipv6/ , https://www.blackhillsinfosec.com/mitm6-strikes-again-the-dark-side-of-ipv6/

## Gotchas

- **Operational safety:** overriding IPv6 DNS breaks normal resolution on IPv4-reliant nets. In a PoC, **whitelist one target** (`-hw`) and stop the tool right after verifying — unconstrained it causes segment-wide outages.
- Only inside an authorised, isolated engagement — see [[Method - Legal and authorization (Belgium)]].

## Detection (SOC)

Suricata/Snort signatures (FOX-IT) for DHCPv6 Advertise and WPAD-DNS-over-IPv6; alert on a new IPv6 DNS server appearing. Watch in Wireshark for unprompted ICMPv6 NS / DHCPv6 Solicit from Windows hosts.

## Related

- [[Network - Rogue DHCP DNS and IPv6 mitm6]]
- [[Tools]]
