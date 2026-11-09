---
tags: [methodology]
phase: [recon]
---
# 1 Recon

Back to [[Methodology]].

**TL;DR:** find the hosts and which ports/services are open, so you know what you're attacking. See [[Recon]], then [[Ports]].

## Checklist

- [ ] Confirm scope and target(s)
- [ ] Ping / host discovery
- [ ] Fast all-ports scan, then a service+version scan on what's open
- [ ] Note every open port in the project State, then open [[Ports]] for each
- [ ] DNS / subdomains if there's a domain

## Notes for this stage

Links to the vault notes that explain these steps (added as we write them).

- [[Recon - OSINT opsec and environment]]: clean VM and evidence handling before starting
- [[Recon - OSINT domain footprint]]: passive domain and infrastructure
- [[Recon - OSINT people and email]]: people, addresses, usernames
- [[Recon - Google dorks and metadata]]: search operators and document metadata
- [[Recon - Breach exposure checks]]: credential exposure, reported in aggregate

OSINT audit extras: get scope and interaction level in writing, compare found assets with the client's list, check what suppliers publish about the client, claim no exploitability the active phase hasn't confirmed, and hand over the queries so the sweep can be repeated.

## Active recon, as a funnel

Authorisation first: systems and ranges, out of scope, window, allowed techniques, third-party infrastructure, emergency contact and stop condition.

1. [[Recon - Host discovery ARP and ICMP]], and [[Recon - IPv6 discovery]] if used
2. [[Recon - Port scanning TCP and UDP]] on live hosts only
3. [[Recon - Service and OS fingerprinting]] on open ports only
4. Keep timestamped pcaps as the audit trail ([[Recon - Wireshark scan filters]])

Deliver one asset inventory per host (IP, MAC/vendor, ports, services and versions, OS), not raw scan output. Handle fragile devices with slower timing or by hand, warn the client before noisy phases, and don't slide into vulnerability checks during recon.
