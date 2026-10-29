---
tags: [methodology]
phase: [lateral]
---
# 5 Lateral movement

Back to [[Methodology]]. Comes after [[Method - 4 Privilege escalation]].

**TL;DR:** use this host to reach others: reuse creds, pivot, move through the domain. See [[Active Directory]] and [[Network]].

## Checklist

- [ ] Loot creds/hashes/keys from this host
- [ ] Spray/reuse them against other hosts and services
- [ ] In AD: enumerate, then kerberoast / pass-the-hash / abuse ACLs — see [[Active Directory]]
- [ ] Set up tunnelling/pivot to reach internal hosts — see [[Network]]
- [ ] Record each new host and cred in the State

## Notes for this stage

Links to the vault notes that explain these steps (added as we write them).
