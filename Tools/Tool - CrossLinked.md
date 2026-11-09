---
tags: [recon, osint]
tools: [crosslinked]
ports: []
os: [linux]
phase: [recon]
familiarity: reference
---
# Tool - CrossLinked

**TL;DR:** Turns LinkedIn employee names from search engine results into likely usernames or emails.

**My take:** Replaces LinkedInt, which no longer works. Needs the email format first (Hunter.io).

from: SE - OSINT (course chapter)

**Get it:** https://github.com/m8sec/CrossLinked

## Install

```bash
pipx install crosslinked
```

## Commands we use

```bash
crosslinked -f '{first}.{last}@<DOMAIN>' '<COMPANY>'
```

## Gotchas

- Output is probable addresses; validate before relying on them.

## Related

- [[Recon]]
- [[Tools]]
