# Privesc

Back to [[Home]].

Getting from a low-privileged user to root or SYSTEM. Names start with `Privesc - Linux` or `Privesc - Windows`.

## Notes

- [[Privesc - Windows enumeration]]: winPEAS + the fast manual wins (whoami /priv, cmdkey, AlwaysInstallElevated)
- [[Privesc - Windows services]]: unquoted paths, weak service perms, writable binaries, DLL hijack → SYSTEM
- [[Privesc - Windows token impersonation]]: SeImpersonate → Potato family (PrintSpoofer/GodPotato/JuicyPotato)
- [[Privesc - Linux enumeration]]: linPEAS + the fast manual wins (sudo -l, SUID find, getcap)
- [[Privesc - Linux sudo and SUID]]: root-owned binaries → GTFOBins shell escapes
- [[Privesc - Linux cron and misc]]: cron scripts/PATH, capabilities, NFS no_root_squash, writable /etc/passwd
