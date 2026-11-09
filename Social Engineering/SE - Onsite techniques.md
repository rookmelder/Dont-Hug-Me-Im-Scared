---
tags: [social-engineering, physical]
tools: []
ports: []
os: []
phase: [recon, initial-access]
---
# SE - Onsite techniques

**TL;DR:** Face-to-face/physical SE. The common thread: a plausible pretext plus a prop (uniform, badge, delivery) gets you past controls that technology alone won't stop. Awareness is the only real fix.

from: SE - Social Engineering course doc

## Techniques

- **Impersonation** — pretend to be staff/authority/contractor (cheap uniform + tools bought online). Non-technical roles (e.g. prospective renter) can be enough to get keycard access.
- **Shoulder surfing** — read PINs/passwords/forms over a shoulder; works at distance with phone cameras/binoculars. Defence: shield keypad, screen privacy filters, back to the wall.
- **Dumpster diving** — trash yields phone lists, org charts, calendars, sticky-note creds — all pretext fuel. Defence: shred, secure/locked bins, equipment decommissioning + data-retention policy, wipe drives and clear TPM before disposal.
- **Tailgating vs piggybacking** — following someone into a restricted area. **Tailgating = without consent**; **piggybacking = the authorised person consents** (holds the door). Defence: turnstiles, mantraps, badge checks, guards — but all fail without an aware "challenge strangers" culture.
- **Badge cloning** — clone RFID access cards with cheap hardware/software, or just fabricate a look-alike badge and rely on people letting you in. Badge designs are often leaked in social-media photos (new-job/leaving posts).
- **Baiting** — leave tempting bait (USB labelled "Salary List 2026" in the car park); curiosity → plugged in → malware. Online bait: free movie, "confidential" doc, gift card.
- **Quid pro quo** — offer a service for info/access ("IT here, give me your login and I'll upgrade your system").

## Related

- [[SE - Psychology principles]]
- [[SE - Attack phases]]
