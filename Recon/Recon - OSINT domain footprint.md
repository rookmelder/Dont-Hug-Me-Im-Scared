---
tags: [recon, osint]
tools: [whois, dig, curl, subfinder, shodan]
ports: []
os: []
phase: [recon]
---
# Recon - OSINT domain footprint

**TL;DR:** Start from a domain and pivot passively through registration, DNS, certificates, scan databases and archives. Zone transfers and subdomain brute force against the target's name servers are active: they need written authorisation.

```bash
whois <DOMAIN>; whois <IP>
dig NS <DOMAIN> +short; dig MX <DOMAIN> +short; dig TXT <DOMAIN> +short
dig TXT _dmarc.<DOMAIN> +short; dig DS <DOMAIN>
curl -s "https://crt.sh/?q=%25.<DOMAIN>&output=json" | jq -r '.[].name_value' | sort -u
curl -s "https://web.archive.org/cdx/search/cdx?url=<DOMAIN>/*&output=txt&fl=original&collapse=urlkey"
```

| Record | Reveals | Angle |
|---|---|---|
| MX | Mail provider, gateway | Which login page a phish would fake |
| SPF | Allowed senders, SaaS list | Too permissive helps spoofing |
| TXT tokens | Services in use | Old tokens show forgotten services |
| DMARC | Failure policy | `p=none` doesn't block spoofed mail |
| CNAME | Cloud targets | Deleted resource may allow subdomain takeover |

Domain creation date is a strong phishing signal. Registrant names are usually hidden since GDPR. For IP blocks in Europe, RIPE is often better than domain whois.

Web: https://apps.db.ripe.net, https://www.dnsbelgium.be, https://dnsdumpster.com, https://securitytrails.com (historic DNS), https://web-check.xyz, https://digger.tools, https://crt.sh, https://sitereport.netcraft.com, https://web.archive.org

Tools: [[Tool - subfinder]], [[Tool - Shodan]], [[Tool - theHarvester]]

from: SE - OSINT (course chapter)

## Related

- [[Recon]]
- [[Method - 1 Recon]]
