---
tags: [active-directory, credentials, lateral]
tools: [impacket]
ports: [445]
os: [windows]
phase: [credential-access, lateral, persistence]
---
# AD - DCSync

**TL;DR:** With an account that has replication rights (Domain Admin, or any account granted DS-Replication-Get-Changes), `secretsdump` uses the DRSUAPI protocol to make the DC replicate **every** password hash — including `krbtgt` and Administrator. Full domain compromise.

from: TryHackMe Attacktive Directory — verified vs Impacket docs

## When to use

You have high-priv creds/hash and want every hash in the domain (NTDS.dit) without touching disk on the DC.

## How

```bash
# Dump all domain hashes via replication
secretsdump.py <DOMAIN>/<USER>:<PASS>@<DC-IP>
# Pass-the-hash instead of a password:
secretsdump.py <DOMAIN>/<USER>@<DC-IP> -hashes <LMHASH>:<NTHASH>
```

Output gives `user:rid:lmhash:nthash:::` — feed Administrator's NT hash into [[AD - Pass-the-hash]].

## Gotchas

- `krbtgt` hash → forge Golden Tickets (persistence).
- Local-only (SAM) dump from a non-DC: same tool, `-sam`.

## Related

- [[AD - Pass-the-hash]], [[AD - Kerberoasting]]
- [[Passwords]]
