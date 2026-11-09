---
tags: [recon, osint]
tools: [shodan]
ports: []
os: [linux]
phase: [recon]
familiarity: reference
---
# Tool - Shodan

**TL;DR:** Searchable index of internet-wide scans: ports, banners, certs, versions.

**My take:** You query their database and send nothing to the target. Censys (https://censys.com) is the alternative.

from: SE - OSINT (course chapter)

**Get it:** https://www.shodan.io (CLI: https://github.com/achillean/shodan-python)

## Install

```bash
pipx install shodan
```

## Commands we use

```bash
# web or CLI filters
hostname:<DOMAIN>
ssl.cert.subject.cn:<DOMAIN>
org:"<ORG>"
```

## Gotchas

- The free account limits filters; cheap lifetime memberships appear occasionally.
- Workflow: CVE, then how the product fingerprints itself, then search for exposed instances.

## Related

- [[Recon]]
- [[Tools]]
