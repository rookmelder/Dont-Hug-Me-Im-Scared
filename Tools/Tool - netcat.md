---
tags: [recon, scanning]
tools: [nc]
ports: []
os: [linux, windows]
phase: [recon, enum]
familiarity: reference
---
# Tool - netcat

**TL;DR:** Raw TCP connection, used here for manual banner grabbing.

**My take:** Shows exactly what the service sends, with nothing interpreted by a scanner.

from: SB - Active RECON (course chapter)

**Get it:** Preinstalled on Kali (nc)

## Install

```bash
sudo apt install netcat-traditional
```

## Commands we use

```bash
nc <IP> <PORT>   # prints the banner if the service sends one
```

## Gotchas

- Connections are unencrypted.
- HTTP sends nothing until you send a request.

## Related

- [[Recon]]
- [[Tools]]
