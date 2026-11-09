---
tags: [recon, osint]
tools: [exiftool]
ports: []
os: []
phase: [recon]
---
# Recon - Image search and geolocation

**TL;DR:** Check metadata first ([[Tool - exiftool]]), reverse-search the image, then geolocate: observe, hypothesise, narrow, confirm, optionally chronolocate.

| Engine | Strength |
|---|---|
| https://images.google.com (Lens) | Objects, landmarks, text |
| https://www.bing.com/visualsearch | Different index |
| https://yandex.com/images | Faces and places, Eastern Europe |
| https://tineye.com | Copies sorted by date: first appearance |

Maps: Google Street View, https://www.openstreetmap.org, https://www.mapillary.com, https://zoom.earth, https://browser.dataspace.copernicus.eu. Sun position: https://www.suncalc.org

- AI geolocation output is a hypothesis to confirm.
- Face search (PimEyes) processes biometric data and is legally loaded in the EU; treat as off-limits without an explicit legal basis.

from: SE - OSINT (course chapter)

## Related

- [[Recon]]
- [[Method - 1 Recon]]
