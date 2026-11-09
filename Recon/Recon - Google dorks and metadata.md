---
tags: [recon, osint]
tools: [exiftool, foca]
ports: []
os: []
phase: [recon]
---
# Recon - Google dorks and metadata

**TL;DR:** Search operators turn an engine into recon, and public documents leak usernames and software through metadata.

| Operator | Example |
|---|---|
| `site:` / `-site:` | `site:<DOMAIN> -site:www.<DOMAIN>` |
| `filetype:` / `ext:` | `site:<DOMAIN> filetype:pdf` |
| `intitle:` | `site:<DOMAIN> intitle:"index of"` |
| `inurl:` | `site:<DOMAIN> inurl:login` |
| `after:` / `before:` | `site:<DOMAIN> after:2025-01-01` |

- Google removed `cache:` in 2024; use the Wayback Machine.
- Bing indexes differently, Yandex is strong on images, DuckDuckGo doesn't personalise.
- Catalogue of dorks: https://www.exploit-db.com/google-hacking-database
- Exposed config or backup on an in-scope domain: report it. Don't use its contents outside your mandate.

Metadata: dork for `filetype:pdf` or `docx`, download, run [[Tool - exiftool]]. [[Tool - FOCA]] automates this on Windows.

from: SE - OSINT (course chapter)

## Related

- [[Recon]]
- [[Method - 1 Recon]]
