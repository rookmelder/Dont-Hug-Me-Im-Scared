---
tags: [network, mitm, layer2]
tools: [arpspoof, bettercap, dsniff, wireshark]
ports: []
os: [linux]
phase: [credential-access, lateral]
---
# Network - ARP cache poisoning

**TL;DR:** ARP has **no authentication** — a host caches whatever ARP reply arrives, even unsolicited (gratuitous). Poison both the victim's and the gateway's caches with your MAC and all their traffic routes through you (MITRE **T1557.002**). Needs Layer-2 access to the segment. IPv6 has the same flaw via NDP — see [[Network - Rogue DHCP DNS and IPv6 mitm6]].

from: SB - Man-in-the-Middle Security & Defense (course chapter)

## When to use

You have L2 connectivity to the target segment (a wall-jack, a rogue drop-box) and the segment uses IPv4 ARP. Flat / unsegmented VLANs are the prime target — especially mixed IT/OT with cleartext services.

## Mechanics (the 5 steps)

1. Recon: find your interface (`ip a`), the gateway (`ip route show`), and victim/server IPs.
2. Forge **gratuitous ARP** replies advertising *your* MAC for the gateway IP and the victim IP.
3. Both caches update → each binds the other's IP to your MAC.
4. Traffic flows through you in both directions.
5. Then sniff, hijack sessions, inject into cleartext downloads, or blackhole for DoS.

## How

```bash
# 1. Enable IP forwarding, or you blackhole the victim (accidental DoS)
sudo sysctl -w net.ipv4.ip_forward=1
sysctl net.ipv4.ip_forward                 # verify = 1
# persist: uncomment net.ipv4.ip_forward=1 in /etc/sysctl.conf

# 2. Poison victim -> gateway  (terminal 1)
# arpspoof -i <IFACE> -t <VICTIM_IP> <GATEWAY_IP>
arpspoof -i eth0 -t <VICTIM_IP> <GATEWAY_IP>

# 3. Poison gateway -> victim  (terminal 2, keep BOTH running)
arpspoof -i eth0 -t <GATEWAY_IP> <VICTIM_IP>
```

`arpspoof` is from the legacy **dsniff** suite. Legacy sniffers on top of an active poison: `driftnet -i eth0` (images from cleartext streams), `urlsnarf` / `filesnarf` (HTTP URLs, plain-text file transfers). Nearly all useless against TLS now — see [[Network - MITM positions and reality]]. [[Tool - bettercap]] does the whole thing (spoof + sniff + proxy) in one tool and is the modern choice.

## Detect / defend

| Control | Blocks | How |
|---|---|---|
| **Dynamic ARP Inspection (DAI)** | ARP poisoning | switch drops ARP replies that fail the DHCP-snooping binding DB |
| **DHCP Snooping** | rogue DHCP (feeds DAI) | only trusted ports may send DHCP offers/acks |
| Ignore gratuitous ARP | unsolicited cache updates | OS ignores unrequested ARP replies |
| Static ARP entries | poisoning of critical links | manual IP↔MAC for gateway/SCADA (impractical at scale) |
| TLS/HTTPS + Kerberos | the *payoff* of interception | encryption + strong auth, not legacy NTLM |
| Segmentation | blast radius | kill flat IT/OT VLANs |

**SOC signs:** one MAC suddenly owns many IPs; a gateway IP's MAC changes; gratuitous-ARP bursts. Catch with `arpwatch`, Zeek, IDS signatures; DAI + DHCP snooping prevent it outright.

## Related

- [[Network - MITM positions and reality]]
- [[Network - Rogue DHCP DNS and IPv6 mitm6]]
- [[Tool - bettercap]]
- [[Network]]
