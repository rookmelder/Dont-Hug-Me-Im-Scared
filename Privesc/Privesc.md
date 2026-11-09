# Privesc

Back to [[Home]].

Getting from a low-privileged user to root or SYSTEM. Names start with `Privesc - Linux` or `Privesc - Windows`.

## Notes

- [[Privesc - Windows enumeration]]: winPEAS + the fast manual wins (whoami /priv, cmdkey, AlwaysInstallElevated)
- [[Privesc - Windows services]]: unquoted paths, weak service perms, writable binaries, DLL hijack → SYSTEM
- [[Privesc - Windows token impersonation]]: SeImpersonate → Potato family (PrintSpoofer/GodPotato/JuicyPotato)
