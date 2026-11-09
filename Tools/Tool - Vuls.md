---
tags: [enum, vuln-scanning]
tools: [vuls]
ports: []
os: [linux]
phase: [enum]
familiarity: reference
---
# Tool - Vuls

**TL;DR:** Open-source, agentless scanner for packages and libraries on Linux/FreeBSD hosts over SSH.

**My take:** Suited to patch-level checks on servers you hold SSH keys for, not to unauthenticated scanning.

from: SB - Vulnerability scanning (course chapter)

**Get it:** https://vuls.io (https://github.com/vulsio/vulsctl, TUI: https://vuls.io/docs/en/usage-tui.html, web UI: https://vuls.io/docs/en/vulsrepo.html)

## Install

```bash
sudo apt install docker.io && sudo systemctl start docker
git clone https://github.com/vulsio/vulsctl.git && cd vulsctl
./update-all.sh          # fetch the vulnerability databases (slow)
ssh-keygen -t rsa && ssh-copy-id -i ~/.ssh/id_rsa.pub <USER>@<HOST>
```

## Commands we use

```bash
# config.toml
# [servers.target]
# host = "<HOST>"
# port = "22"             # or "local" for localhost
# user = "<USER>"
# keyPath = "<KEYFILE>"
# scanMode = [ "fast" ]   # fast, fast-root or deep
./scan.sh && ./report.sh
./tui.sh                  # terminal viewer
./vulsrepo.sh             # web UI on port 5111
```

## Gotchas

- SSH password authentication isn't supported; use keys.
- The source edits `$HOME/vuls/config.toml`; check which path your vulsctl scripts read.

## Related

- [[Recon - Vulnerability scanning overview]]
- [[Tools]]
