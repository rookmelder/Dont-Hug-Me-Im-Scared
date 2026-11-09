---
tags: [enum, vuln-scanning]
tools: [openvas, gvm]
ports: []
os: [linux]
phase: [enum]
familiarity: reference
---
# Tool - OpenVAS

**TL;DR:** Open-source network vulnerability scanner (Greenbone GVM) with a large test feed.

**My take:** The free full scanner. Give it credentials when in scope for far better results.

from: SB - Vulnerability scanning (course chapter)

**Get it:** https://www.kali.org/tools/gvm/ (Kali guide: https://greenbone.github.io/docs/latest/22.4/kali/index.html, trial VM: https://www.greenbone.net/en/testnow/, test catalogue: https://secinfo.greenbone.net/nvts, demo: https://livedemo.greenbone.net/)

## Install

```bash
sudo apt update && sudo apt upgrade
sudo apt install gvm
sudo gvm-setup        # note the generated admin password at the end
sudo gvm-check-setup
```

## Commands we use

```bash
# browse to https://localhost:9392, log in as admin
# Scans > Tasks to run, Scans > Reports for results
# Assets > Hosts sorted by severity shows the worst first
```

## Gotchas

- First setup downloads the feed and takes a long time.
- To listen on an external interface, edit the Greenbone Security Assistant systemd unit (the source names `greenbone-security-assistant.service`; check the name on your version).

## Related

- [[Recon - Vulnerability scanning overview]]
- [[Tools]]
