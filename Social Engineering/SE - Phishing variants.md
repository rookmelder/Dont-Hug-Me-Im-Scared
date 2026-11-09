---
tags: [social-engineering, phishing]
tools: [set]
ports: []
os: []
phase: [initial-access]
---
# SE - Phishing variants

**TL;DR:** Phishing = posing as a trusted entity to get creds/money/action, usually via a fake site matching the real one's look. The variants are just the channel and targeting.

from: SE - Social Engineering course doc

## By targeting

- **Spam / mass phishing** — non-personalised, cast wide, catch anyone.
- **Spear phishing** — personalised to specific individuals; much higher hit rate.
- **Whaling** — spear phishing aimed at high-value targets (CEO/CFO, execs, officials).

## By channel

- **Vishing** — voice/phone. Now boosted by AI voice cloning (impersonate family/boss from a short sample) and caller-ID spoofing.
- **Smishing** — SMS.
- **Quishing** — malicious QR codes for credential harvesting / malware (QR dodges URL inspection and email link filters).
- **Deepfakes** — AI video, now possible live on video calls → next-gen phishing over video conference.

## Related tactics

- **Pretexting** — the invented identity/scenario underneath the phish (fake customer-service rep, etc.).
- **Scareware** — fake "you're infected" pop-ups driving a click/purchase.

## Footprinting (prep)

Gather before phishing: WHOIS/registration + contacts, harvested emails, IP range, active hosts, DNS records, subdomains, OS fingerprint, login pages. See [[Tool - emailharvester]].

## Delivery / cred harvesting

[[Tool - SET]] clones a login page and captures entered creds — the classic lab demo.

## Bypassing MFA (AITM)

Adversary-in-the-middle phishing kits proxy the real login page so they capture the **session cookie/token after MFA**, not just the password — defeating ordinary TOTP/push MFA. Sold as kits/services on dark web markets. Defence: phishing-resistant MFA (FIDO2/WebAuthn/passkeys), which binds the credential to the real origin. Context: credential abuse ("they don't break in, they log in") and infostealer malware are now top initial-access vectors alongside phishing.

## Countermeasures

Staff training + phishing simulations, report channel for suspicious mail, and technical anti-phishing filtering (SPF/DKIM/DMARC, link rewriting).

## Related

- [[SE - Psychology principles]]
- [[SE - Attack phases]]
- [[Recon]]
