---
tags: [network, dos, ddos]
tools: [hping3, slowloris]
ports: []
os: []
phase: [exfil]
---
# Network - DoS and DDoS

**TL;DR:** Denial of service attacks the **availability** leg of CIA: exhaust a resource (bandwidth, connection state, CPU, threads) so real users can't be served. In an audit, DoS is almost always **out of scope** unless a stress test is explicitly contracted — it breaks things and reaches shared infrastructure. Know how each class works so you can recognise and defend against it.

from: SB - (D)DoS attacks (course chapter)

## Three classes

| Class | Measured in | Exhausts | Examples |
|---|---|---|---|
| Protocol | packets/sec | Connection-state tables on servers, firewalls, load balancers | SYN flood, Ping of Death, LAND, Smurf |
| Volumetric | bits/sec | Link bandwidth | ICMP/UDP floods, NTP/DNS/CharGEN/SSDP amplification |
| Application layer | requests/sec | Web server workers/threads, CPU | HTTP flood, Slowloris, R.U.D.Y, ReDoS, zero-day |

## How the main ones work

- **SYN flood** — send many TCP SYNs, never complete the handshake (often with spoofed source IPs). The target holds half-open connections until its backlog fills. *Defence:* SYN cookies, backlog tuning, rate limiting.
- **Reflection** — spoof the victim's IP as the source of requests to public UDP services; the services reply **to the victim**. Hides the attacker and uses legitimate servers.
- **Amplification** — pick a service whose reply is far bigger than the request. Rough factors: NTP `monlist` ~556×, CharGEN ~359×, DNS ~28–54×, SSDP ~31×. *Defence:* don't expose these services; disable NTP `monlist`; filter spoofed source IPs at the edge (BCP 38 / uRPF).
- **ICMP / UDP flood** — raw packet volume; UDP floods also make the host emit ICMP "port unreachable" for closed ports.
- **Ping of Death** — oversized/malformed ping overflows reassembly on old stacks; obsolete but the template for malformed-packet crashes.
- **Smurf / Smurf6** — ICMP echo to a broadcast (IPv4) or multicast (IPv6) address with the victim as spoofed source, so every host replies to the victim. IPv4 is mitigated on modern gear; IPv6 multicast can still bite.
- **LAND** — a packet whose source = destination (same IP and port); old stacks loop.
- **HTTP flood** — many valid-looking HTTP requests; hard to filter because each request is legitimate.
- **Slowloris / R.U.D.Y** — "low and slow": open many connections and send headers (Slowloris) or a POST body (R.U.D.Y) a few bytes at a time to hold worker threads open. Tiny bandwidth, kills threaded servers. *Defence:* connection timeouts, limits per IP, an event-driven proxy (nginx) in front.
- **ReDoS** — feed input that makes a vulnerable regex backtrack exponentially; one request pins a CPU. See https://owasp.org/www-community/attacks/Regular_expression_Denial_of_Service_-_ReDoS
- **Yo-yo** — against autoscaling: flood until it scales out, stop until it scales in, repeat. Drives cost and degrades service cheaply.
- **Blacknurse** — low-bandwidth ICMP Type 3 Code 3 that spikes CPU on some firewalls; block/limit that ICMP type outbound.

## Detection

- One source (or a few) hitting one host hard: see [[Recon - Wireshark scan filters]] for the filters; a SYN flood is `tcp.flags.syn==1 && tcp.flags.ack==0` in a flood with no completing ACKs.
- Half-open connections piling up (`netstat`/`ss` showing many `SYN_RECV`).
- A burst of ICMP Type 3 Code 3 or echo traffic from/to one address.
- Quick single-IP check on Linux: group connections by source IP from `ss`/`netstat` and look for an outlier (see the TechRepublic how-to in [[Network - DDoS defences and tools]]).

## Related

- [[Network]]
- [[Network - DDoS defences and tools]]
- [[Recon - Wireshark scan filters]]
