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
- [ ] Search versions for known exploits — see [[Exploitation]]
- [ ] Record every finding in the project State

## Notes for this stage

Links to the vault notes that explain these steps (added as we write them).
