---
tags: [privesc, enum]
tools: [linpeas]
ports: []
os: [linux]
phase: [privesc]
---
# Privesc - Linux enumeration

**TL;DR:** Run linPEAS for the full sweep, but hit the fast wins by hand first: `sudo -l`, SUID search, and `getcap`. Those three cover most CTF/real boxes.

from: TryHackMe Linux PrivEsc / PrivEsc Arena — verified vs common Linux LPE references

## Quick manual checks (do these first)

```bash
id; sudo -l                         # what can I run as root? -> GTFOBins
find / -perm -4000 -type f 2>/dev/null   # SUID binaries -> GTFOBins
getcap -r / 2>/dev/null             # file capabilities (cap_setuid = root)
cat /etc/crontab; ls -la /etc/cron.*     # root cron jobs
uname -a                            # kernel version -> exploit suggester
ls -la /home/*; cat ~/.*history 2>/dev/null   # creds/keys lying around
```

## Full sweep

```bash
./linpeas.sh | tee linpeas.out      # read the red/yellow hits
# alternatives: linux-exploit-suggester.sh, lse.sh (Linux Smart Enumeration)
```

## Related

- [[Privesc - Linux sudo and SUID]], [[Privesc - Linux cron and misc]]
- GTFOBins: https://gtfobins.github.io
- Alternative scripts: LinEnum https://github.com/rebootuser/LinEnum, linux-smart-enumeration https://github.com/diego-treitos/linux-smart-enumeration
