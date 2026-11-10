---
tags: [methodology, legal]
tools: []
ports: []
os: []
phase: []
---
# Method - Legal and authorization (Belgium)

**TL;DR:** The technique is neutral; the **authority is everything**. A signed engagement with a defined scope is your only authority, and only *within* that scope. Interception (MITM/AiTM) is especially sensitive because it also engages the secrecy of communications, not just "ordinary" hacking. Outside a formal engagement, the lawful move for a real finding is to report it through the **CCB CVD** procedure — not to prove it further.

from: SB - Man-in-the-Middle Security & Defense (course chapter)

## The three Belgian anchors

- **Unauthorised access & data/system interference** — criminal offences. Historically Computer Crime Act of 28 Nov 2000 (Criminal Code art. 550bis/550ter). Note: Belgium's **new Criminal Code enters into force on 1 September 2026**, which renumbers/restructures these provisions.
- **Secrecy of communications** — intercepting communications engages protections *beyond* ordinary hacking. MITM is interception by definition; treat it as the more sensitive act it is.
- **CCB safe harbour (Coordinated Vulnerability Disclosure)** — since **15 Feb 2023**, Belgium protects a reporter who meets *all* conditions: report in writing to the CCB *and* the affected organisation as soon as possible; no fraudulent intent or malice; stay **proportionate** (go no further than needed to confirm); and do not disclose publicly without the CCB's agreement.

## Scope and proportionality (the one that matters most)

The moment interception would touch anything outside scope — a real user's live credentials, a neighbouring organisation, the public network — you **stop and document**; you do not continue "to be thorough". Proportionality isn't politeness, it's the legal condition that keeps you on the right side of the line.

- **Lawful interception ≠ private assessment.** Interception by authorities runs on warrants and procedures that do **not** transfer to your engagement.
- **Evidence integrity.** Interception captures are evidence: record hashes, time, and chain of custody.
- **NIS2 duties.** Essential/important entities (utilities, etc.) have incident-notification duties to national authorities; a MITM on such a network is a reportable, regulated incident, not just a technical finding.

## Related

- [[Network - MITM positions and reality]]
- [[AD - LLMNR and NBT-NS poisoning]]
- [[Methodology]]
