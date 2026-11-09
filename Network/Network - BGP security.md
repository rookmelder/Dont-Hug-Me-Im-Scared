---
tags: [network, bgp]
tools: [bgpalerter]
ports: [179]
os: []
phase: [recon]
---
# Network - BGP security

**TL;DR:** BGP routes between autonomous systems and trusts what neighbours announce, so false or mistaken routes can spread. RPKI validates who may originate a prefix; BGPsec signs the path but is hard to deploy.

from: Tracing the path (course chapter)

## Failure types

| Type | What happens | Example |
|---|---|---|
| Prefix hijack | An AS announces a prefix it doesn't own | Amazon DNS prefixes, 2018 |
| Route leak | Misconfiguration announces beyond the intended scope | Rostelecom AS12389, 2020 |
| Accidental hijack | Local filtering escapes | Pakistan and YouTube, 2008 |
| Self-inflicted outage | A config change withdraws reachability | Facebook, 2021 |

BGP runs over TCP, so peer sessions are also exposed to classic TCP/IP attacks. Peer authentication doesn't stop bad data from a legitimate peer.

## Monitoring and checks

- Is an ISP filtering yet: https://isbgpsafeyet.com
- Route history: https://stat.ripe.net/special/bgplay
- Incidents: https://bgpstream.com
- Own-prefix alerts (hijack, visibility, RPKI, ROA expiry): https://github.com/nttgin/BGPalerter
- Operator norms: https://observatory.manrs.org
- Standards: RPKI https://datatracker.ietf.org/doc/html/rfc6480 and https://datatracker.ietf.org/doc/html/rfc8360, BGPsec https://datatracker.ietf.org/doc/html/rfc8205
- Background: https://www.cloudflare.com/learning/security/glossary/what-is-bgp/, https://www.catchpoint.com/blog/bgp-vulnerabilities

Never announce or manipulate routes during a test unless that is explicitly in scope: the effect reaches other networks.

## Related

- [[Network]]
- [[Recon - Tracing the path and ASNs]]
