---
tags: [active-directory, enum]
tools: [kerbrute, enum4linux-ng, netexec, nmap]
ports: [88, 139, 389, 445, 464, 636, 3268, 5985]
os: [windows]
phase: [recon, enum]
---
# AD - Enumeration

**TL;DR:** Against a DC, first map the AD ports, pull the domain/FQDN, then enumerate valid usernames. `kerbrute userenum` is the quiet win: it validates users via Kerberos pre-auth without logging failed logons the same way.

from: TryHackMe Attacktive Directory — verified vs common AD writeups

## When to use

Open 88 (Kerberos) + 389/445 on a Windows host = domain controller. Start here before any attack.

## How

```bash
# Port/service + SMB/LDAP scripts; grab the domain + hostname
nmap -p88,139,389,445,464,636,3268,5985 -sV --script "smb-os-discovery,ldap-rootdse" <DC-IP>

# SMB / null-session enum (shares, users, domain, password policy)
enum4linux-ng -A <DC-IP>
nxc smb <DC-IP> -u '' -p '' --shares        # null session
nxc smb <DC-IP> -u <USER> -p <PASS> --users

# Validate usernames over Kerberos (needs the realm FQDN)
kerbrute userenum -d <DOMAIN> --dc <DC-IP> <USERLIST>
```

## Gotchas

- kerbrute needs the **domain FQDN** (e.g. `spookysec.local`), not the NetBIOS name. Get it from `smb-os-discovery` or ldap rootDSE.
- Valid users found here feed straight into [[AD - AS-REP roasting]] and [[AD - Kerberoasting]].

## Related

- [[AD - AS-REP roasting]], [[AD - Kerberoasting]]
- [[Tool - netexec]], [[Ports]]
