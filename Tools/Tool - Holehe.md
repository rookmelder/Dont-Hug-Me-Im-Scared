---
tags: [recon, osint]
tools: [holehe]
ports: []
os: [linux]
phase: [recon]
familiarity: reference
---
# Tool - Holehe

**TL;DR:** Checks which services an email address is registered with.

**My take:** Web alternative: Epieos (https://epieos.com). Only with authorisation for that person's address.

from: SE - OSINT (course chapter)

**Get it:** https://github.com/megadose/holehe

## Install

```bash
pipx install holehe
```

## Commands we use

```bash
holehe <EMAIL>
```

## Gotchas

- **Not passive:** it touches the services' signup or password-reset functions.

## Related

- [[Recon]]
- [[Tools]]
