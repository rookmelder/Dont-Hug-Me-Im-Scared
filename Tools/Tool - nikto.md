---
tags: [enum, vuln-scanning]
tools: [nikto]
ports: []
os: [linux]
phase: [enum]
familiarity: go-to
---
# Tool - nikto

**TL;DR:** Web server scanner: dangerous files, outdated versions, config issues.

**My take:** First web probe. Very loud, so only where noise is acceptable.

from: SB - Vulnerability scanning (course chapter)

**Get it:** https://github.com/sullo/nikto (wiki: https://github.com/sullo/nikto/wiki, https://cirt.net/Nikto2)

## Install

```bash
sudo apt install nikto
```

## Commands we use

```bash
nikto -h <HOST> -p <PORT>
nikto -list-plugins
nikto -h <HOST> -Plugins '<PLUGIN>'
nikto -h <HOST> -output ./result.csv -Format csv
```

## Gotchas

- Not stealthy: obvious in logs and to IDS/IPS. LibWhisker anti-IDS options exist.
- OSVDB references no longer resolve because that database is offline. Map them with http://cve.mitre.org/data/refs/refmap/source-OSVDB.html or search the finding text.

## Related

- [[Recon - Vulnerability scanning overview]]
- [[Tools]]
