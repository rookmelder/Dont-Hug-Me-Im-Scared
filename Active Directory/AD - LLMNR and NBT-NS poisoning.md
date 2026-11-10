---
tags: [active-directory, mitm, credentials]
tools: [responder, nmap, netexec]
ports: [137, 445, 5355]
os: [windows]
phase: [credential-access, lateral]
---
# AD - LLMNR and NBT-NS poisoning

**TL;DR:** When a Windows host can't resolve a name via DNS it falls back to the broadcast protocols **LLMNR** (5355) and **NBT-NS** (137) — which, like ARP, trust whoever answers. Answer them and the victim hands you **NTLMv2** auth material; if SMB signing isn't required you can **relay** it onward to a service that accepts it (MITRE **T1557.001**). A single GPO closes the whole family.

from: SB - Man-in-the-Middle Security & Defense (course chapter)

## Mechanism

1. Victim mistypes/queries a name that DNS can't resolve (typo, stale share, WPAD).
2. It broadcasts an LLMNR/NBT-NS request to the segment.
3. The attacker (**Responder**) answers "that's me" → victim tries to authenticate → attacker captures the NTLMv2 challenge/response (crack offline) or **relays** it live to another host.
4. **SMB relay:** if the target doesn't *require* SMB signing, the relayed auth lands as the user — straight to shares or admin. This connects to the rest of the [[Active Directory]] chain ([[AD - Pass-the-hash]], etc.).

Often reached first via IPv6/WPAD — see [[Network - Rogue DHCP DNS and IPv6 mitm6]].

> Capturing/relaying live credentials is only lawful inside an authorised, isolated engagement — in a real assessment, prove the pre-conditions exist and report, don't relay against live identities. See [[Method - Legal and authorization (Belgium)]].

## Non-destructive audit (no Responder on a live net)

```bash
# SMB signing: supported vs required (445). "supported but not required" = relay-vulnerable
nmap --script smb-security-mode,smb2-security-mode -p 445 <TARGET_OR_SUBNET>
```

```powershell
# On a file server / DC: RequireSecuritySignature False = not enforced = vulnerable
Get-SmbServerConfiguration | Select-Object EnableSecuritySignature, RequireSecuritySignature
```

- **LLMNR:** GPO *Turn off multicast name resolution* = **Enabled** means LLMNR is off. Registry: `HKLM\Software\Policies\Microsoft\Windows NT\DNSClient\EnableMulticast` = `0` (off).
- **NBT-NS:** check NetBIOS over TCP/IP is Disabled on adapters or via DHCP scope option.
- **Passive:** Wireshark filter `llmnr || nbns` — any multicast name queries confirm the legacy fallback is live.

## Defend

- **Disable LLMNR and NBT-NS** via GPO: *Computer Configuration → Administrative Templates → Network → DNS Client → Turn off multicast name resolution*; disable NetBIOS over TCP/IP.
- **Require SMB signing** via GPO: *Microsoft network server: Digitally sign communications (always)* — neutralises relay outright.
- Segment so broadcast queries don't reach untrusted hosts.

**SOC signs:** LLMNR/NBT-NS answers from an unexpected host; unusual SMB auth patterns. Catch with Zeek + Windows event correlation in the SIEM; prevent by disabling the protocols + SMB signing.

## Related

- [[Network - MITM positions and reality]]
- [[AD - Pass-the-hash]]
- [[Method - Legal and authorization (Belgium)]]
- [[Active Directory]]
