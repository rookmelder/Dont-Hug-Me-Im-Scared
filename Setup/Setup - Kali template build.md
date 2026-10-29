---
tags: [setup, kali, template]
tools: [claude-code]
ports: []
os: [linux]
phase: []
---
# Setup - Kali template build

**TL;DR:** The rebuild recipe for the Kali lab box. Everything installed on the box lives here as runnable commands. Rebuild the template by running through this on a fresh Kali install, then snapshot. **Every new install goes in this file** (see the rule in `CLAUDE.md`).

## How to rebuild the template

1. Fresh Kali VM, then: `sudo apt update && sudo apt full-upgrade -y`
2. Run through the sections below top to bottom.
3. Clear shell history, power off, make the snapshot. See [[Setup - Kali box]].

## System

```bash
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y open-vm-tools-desktop   # VirtualBox: virtualbox-guest-x11
```

## Claude Code + vault

```bash
# Claude Code (native installer)
curl -fsSL https://claude.ai/install.sh | bash
# GitHub CLI (Kali repo lacks it — add GitHub's apt repo; see Setup - Kali box / earlier notes)
sudo apt install -y gh && gh auth login
# Clone the vault
gh repo clone rookmelder/Dont-Hug-Me-Im-Scared ~/DHMIS
```

## Claude Code plugins

```bash
# run these inside a `claude` session
# /plugin marketplace add HeyCubit/effortless
# /plugin install effortless@effortless
# /plugin install context7@...   (hosted MCP; add its marketplace if needed)
```

## Config

Passwordless sudo so Claude Code can run installs — see [[Setup - Kali box]].

## Tools

Add tools here as you install them.

## New installs log

Append every new install here with the date and the exact command, newest on top. Move it up into the right section above when you next rebuild.

- (nothing yet)

## Related

- [[Setup - Kali box]]
