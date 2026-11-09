---
tags: [recon, osint]
tools: [exiftool]
ports: []
os: [linux, windows, macos]
phase: [recon]
familiarity: reference
---
# Tool - exiftool

**TL;DR:** Reads metadata from documents and images: authors, software, internal paths, GPS.

**My take:** Preferred over [[Tool - FOCA]]: a dork plus exiftool does the same job transparently.

from: SE - OSINT (course chapter)

**Get it:** https://exiftool.org

## Install

```bash
sudo apt install libimage-exiftool-perl
```

## Commands we use

```bash
exiftool <FILE>
exiftool -Author -Creator -Producer -r ./downloads/
```

## Gotchas

- Most social platforms strip metadata; files sent as attachments and many websites keep it.

## Related

- [[Recon]]
- [[Tools]]
