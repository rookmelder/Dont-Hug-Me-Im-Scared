---
tags: [recon, network]
tools: [mtr, tracert]
ports: []
os: []
phase: [recon]
---
# Recon - Tracing the path and ASNs

**TL;DR:** Work out who owns an IP (prefix, ASN, ISP) and read a trace for peering, CDNs, exchange points and long-haul links.

from: Tracing the path (course chapter)

## Reading a trace ([[Tool - mtr]])

| You see | It suggests |
|---|---|
| ISP straight into a hosting network | Direct peering |
| Path ends at Akamai or similar | CDN: the IP isn't the origin server |
| Hop named after an exchange (e.g. BNIX) | Networks meeting at an IXP |
| Sudden large RTT jump between hops | Long-distance link such as a sea cable |

Address chain: IANA, then the regional registry (RIPE in Europe), then the local registry or ISP, then the customer.

ISP tiers: Tier 1 reaches everything by settlement-free peering, Tier 2 peers and buys transit, Tier 3 is access to end users ("eyeball" networks).

## Lookups

- Your public IP: https://ifconfig.me, https://www.whatismyip.com, https://ipchicken.com, http://monip.org
- ASN and prefix: https://ipctl.io, https://bgp.he.net, https://bgpview.io, https://www.whatismyip.com/asn/5432/ (swap the number)
- By country: https://ipctl.io/country. Threat map: https://ipctl.io/threat-map
- Registries: https://www.ripe.net/manage-ips-and-asns, https://www.iana.org/assignments/ipv4-address-space/ipv4-address-space.xhtml
- Routing data: https://stat.ripe.net/app/launchpad/, https://thyme.apnic.net
- Exchanges and cables: https://bnix.net, https://www.submarinecablemap.com

## Related

- [[Recon]]
- [[Network - BGP security]]
- [[Recon - OSINT domain footprint]]
