# Active Directory

Back to [[Home]].

Domain enumeration and attacks. Notes are named `AD - <technique>.md`.

Typical chain: [[AD - Enumeration]] → [[AD - AS-REP roasting]] / [[AD - Kerberoasting]] → crack → [[AD - Pass-the-hash]] / [[AD - DCSync]] → domain.

## Notes

- [[AD - Enumeration]]: map the DC, pull the domain FQDN, validate usernames (kerbrute/nxc/enum4linux-ng)
- [[AD - AS-REP roasting]]: grab crackable hashes for pre-auth-disabled accounts, no creds needed
- [[AD - Kerberoasting]]: any domain user → service-account hashes via SPN tickets
- [[AD - DCSync]]: replicate every domain hash (incl. krbtgt) with secretsdump
- [[AD - Pass-the-hash]]: authenticate with an NT hash, no cracking
