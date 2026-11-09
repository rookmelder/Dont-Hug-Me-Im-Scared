---
tags: [social-engineering, phishing]
tools: [set]
ports: []
os: [linux]
phase: [initial-access]
familiarity: reference
---
# Tool - SET

**TL;DR:** The Social-Engineer Toolkit (TrustedSec). Menu-driven framework for SE attacks; most-used piece is the credential harvester that clones a login page and logs whatever's typed in.

**My take:** Lab/demo and authorised phishing engagements only. Pre-installed on Kali. Menu-driven, no flags to remember.

## Install

```bash
# Already on Kali. Elsewhere:
# git clone https://github.com/trustedsec/social-engineer-toolkit
```

## Commands we use

```bash
# Launch
sudo setoolkit
# Credential harvester + site cloner path:
#   1) Social-Engineering Attacks
#   2) Website Attack Vectors
#   3) Credential Harvester Attack Method
#   2) Site Cloner
#   <listener IP>  (default = this VM)
#   <URL to clone> e.g. https://github.com/login
# Victim browses to the IP, enters creds -> captured live.
# Report XML: /root/.set/reports
```

## Gotchas

- Cloned page is served over HTTP on your IP — a real target notices the wrong URL / no TLS; fine for labs.
- Only use against assets you're authorised to test.

## Related

- [[Tools]]
