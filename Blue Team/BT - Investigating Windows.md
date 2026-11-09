---
tags: [blue-team, dfir, ir]
tools: []
ports: []
os: [windows]
phase: []
---
# BT - Investigating Windows

**TL;DR:** Live triage of a possibly-compromised Windows host: who's logged in, what persists (accounts, scheduled tasks, services, Run keys), what's connecting out, and what the logs say. Offensively, this is the checklist that catches your persistence.

from: TryHackMe Investigating Windows — verified vs common Windows IR workflow

## Triage checklist

```cmd
:: Accounts & admins (rogue account? unexpected admin?)
net user
net localgroup administrators
query user                       :: who is logged on

:: Persistence
schtasks /query /fo LIST /v      :: malicious scheduled tasks
reg query HKLM\Software\Microsoft\Windows\CurrentVersion\Run
reg query HKCU\Software\Microsoft\Windows\CurrentVersion\Run
wmic service get name,pathname,startmode

:: Network
netstat -ano                     :: odd outbound / listeners -> PID
tasklist /svc                    :: map PID to process/service

:: Logs
:: Event Viewer / wevtutil: 4624/4625 logons, 4720 user created,
:: 4698 scheduled task created, 7045 service installed, 1102 log cleared
```

## What to look for

- Accounts you didn't expect in the Administrators group.
- Scheduled task / service pointing at a script or odd path = persistence.
- A listener or beaconing connection tied to a suspicious PID.
- Log-cleared events (1102) = attacker covering tracks.

## Related

- [[BT - Windows forensics]], [[BT - SIEM]], [[BT - Kill chains]]
