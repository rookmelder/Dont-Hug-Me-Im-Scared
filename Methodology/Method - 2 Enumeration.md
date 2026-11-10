---
tags: [methodology]
phase: [enum]
---
# 2 Enumeration

Back to [[Methodology]]. Comes after [[Method - 1 Recon]].

**TL;DR:** dig into each open service for a way in: versions, config, content, default creds. The stage where most footholds are found.

## Checklist

- [ ] For each service, read its [[Ports]] row and enumerate it (SMB shares, FTP anon, SNMP, etc.) — see [[Network]]
- [ ] Web apps: directory/vhost brute force, tech stack, logins, params — see [[Web]]
- [ ] Look for default/weak creds and exposed files
- [ ] Search versions for known exploits — see [[Recon - CVE and vulnerability databases]] and [[Exploitation]]
- [ ] Record every finding in the project State

## Notes for this stage

Links to the vault notes that explain these steps (added as we write them).

- [[Recon - Vulnerability scanning overview]]: run scanners against the recon inventory, authenticated where in scope
- [[Recon - Vulnerability scanning links]]: scanner lists and AD, container and code assessment tools
- [[Recon - CVE and vulnerability databases]]: turn a service + version into a CVE and a public PoC
- [[Recon - EUVD European vulnerability database]]: EU vulnerability database, actively-exploited view for prioritising
