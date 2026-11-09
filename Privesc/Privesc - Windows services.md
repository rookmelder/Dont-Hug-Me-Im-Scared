---
tags: [privesc]
tools: [winpeas]
ports: []
os: [windows]
phase: [privesc]
---
# Privesc - Windows services

**TL;DR:** Services run as SYSTEM. If you can control what a service runs — a writable binary, a weak service config, or an unquoted path with a writable gap — you get SYSTEM when it (re)starts. DLL hijacking is the same idea via a missing DLL.

from: TryHackMe Windows PrivEsc / PrivEsc Arena — verified vs common Windows LPE references

## The vectors

**Unquoted service path** — path has spaces and no quotes (`C:\Program Files\My Service\svc.exe`). Windows tries `C:\Program.exe`, `C:\Program Files\My.exe`, … Plant your exe in a writable gap.
```cmd
wmic service get name,pathname,startmode | findstr /i /v "C:\Windows\\" | findstr /i /v """
```

**Weak service permissions** — you can reconfigure the service to run your binary:
```cmd
accesschk.exe /accepteula -uwcqv <USER> *      :: find SERVICE_CHANGE_CONFIG / SERVICE_ALL_ACCESS
sc config <SVC> binPath= "C:\temp\rev.exe"
sc stop <SVC> & sc start <SVC>
```

**Writable service binary** — just overwrite the exe the service launches, then restart it.

**DLL hijacking** — service loads a DLL it can't find on its path; drop a malicious one there.

## Gotchas

- Need restart rights, or a service set to auto-start (reboot) / that you can stop+start.
- `binPath=` needs the space after `=`.

## Related

- [[Privesc - Windows enumeration]], [[Privesc - Windows token impersonation]]
