---
tags: [recon, osint]
tools: [curl, sha1sum]
ports: []
os: []
phase: [recon]
---
# Recon - Breach exposure checks

**TL;DR:** Checking whether an address or domain was exposed is fine. Downloading, buying or logging in with leaked credentials is a different legal matter: stay on the check side unless your mandate says otherwise. Report exposure in aggregate.

Data types: breach dumps (reuse risk), combolists (credential stuffing), infostealer logs (passwords and session cookies with URLs; cookies can bypass MFA).

```bash
# k-anonymity: only the first 5 hash characters leave the machine
echo -n '<PASSWORD>' | sha1sum
curl -s https://api.pwnedpasswords.com/range/<FIRST5>
```

Services: https://haveibeenpwned.com (domain search, stealer logs, Pwned Passwords), https://www.politie.nl/checkjehack, https://scatteredsecrets.com. Monitoring: https://flare.io, https://spycloud.com, https://www.3point.be/offer/pointguard/

from: SE - OSINT (course chapter)

## Related

- [[Recon]]
- [[Method - 1 Recon]]
