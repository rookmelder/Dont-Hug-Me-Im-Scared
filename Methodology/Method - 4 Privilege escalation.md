---
tags: [methodology]
phase: [privesc]
---
# 4 Privilege escalation

Back to [[Methodology]]. Comes after [[Method - 3 Initial access]].

**TL;DR:** go from the foothold user to root / SYSTEM. See [[Privesc]].

## Checklist

- [ ] Run an enum script for your OS (linpeas / winpeas) and read it
- [ ] Check: sudo rights, SUID, cron, services, writable paths, kernel version
- [ ] Look for creds in files, history, config
- [ ] Try the most promising vector; search it in [[Privesc]]
- [ ] Record the new access in the State

## Notes for this stage

Links to the vault notes that explain these steps (added as we write them).
