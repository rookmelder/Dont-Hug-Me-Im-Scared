---
tags: [enum, vuln-scanning]
tools: [testssl]
ports: []
os: [linux]
phase: [enum]
familiarity: reference
---
# Tool - testssl.sh

**TL;DR:** Checks any TLS service's protocols, ciphers and known crypto flaws from the command line.

**My take:** Works on any port, not just 443.

from: SB - Vulnerability scanning (course chapter)

**Get it:** https://testssl.sh (https://github.com/drwetter/testssl.sh)

## Install

```bash
git clone --depth 1 https://github.com/drwetter/testssl.sh.git
```

## Commands we use

```bash
cd testssl.sh && ./testssl.sh <HOST>:<PORT>
```

## Gotchas

- Run it from inside the cloned directory.

## Related

- [[Recon - Vulnerability scanning overview]]
- [[Tools]]
