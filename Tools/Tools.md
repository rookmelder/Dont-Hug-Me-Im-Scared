# Tools

Back to [[Home]].

One note per tool: what it's for, the commands we use and gotchas. Named `Tool - <name>.md`.

## My go-to toolkit (use these first)

The default tool for each phase — the one I already know and have played with. A new chat should reach for these before anything else, and only introduce something new when these don't fit (and say so). Each tool note carries a `familiarity:` field: **go-to** (default to it), **learning** (still getting comfortable), **reference** (documented, not adopted).

> Starting defaults below — **confirm or swap** them for what you actually use, then I'll mark each note and write the ones that are missing.

| Phase | Go-to | Also know / learning |
|---|---|---|
| recon / enum | nmap | autorecon, rustscan |
| web enum | ffuf | gobuster, feroxbuster |
| web probe | nikto, whatweb | |
| AD / SMB enum | netexec (nxc) | enum4linux-ng |
| AD graph | bloodhound | |
| initial access | searchsploit, metasploit | hydra |
| win shell | evil-winrm | |
| privesc (linux) | linpeas | pspy |
| privesc (win) | winpeas | |
| creds / lateral | impacket | netexec |
| password cracking | hashcat | john |

Find every go-to tool with `grep -rl "familiarity: go-to" Tools/`.

## Notes

- [[Tool - SET]]: Social-Engineer Toolkit — credential harvester / site cloner (reference)
- [[Tool - emailharvester]]: domain email harvesting for footprinting (reference)
