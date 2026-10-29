---
tags: [setup, kali, sudo]
tools: [claude-code]
ports: []
os: [linux]
phase: []
---
# Setup - Kali box

**TL;DR:** The Kali lab VM has **passwordless sudo**, so Claude Code can run `sudo` commands (apt installs, tooling) without hanging on a hidden password prompt. Lab VM only — never on a machine that matters or is shared.

## Why

Claude Code runs commands non-interactively, so a `sudo` password prompt just hangs. Passwordless sudo removes the prompt so installs and sudo tooling work unattended.

## How it's set

One of these (type the password once when running it). Scoped to package managers is safer:

```bash
# Scoped (recommended): only apt/dpkg
echo "$USER ALL=(ALL) NOPASSWD: /usr/bin/apt, /usr/bin/apt-get, /usr/bin/dpkg" | sudo tee /etc/sudoers.d/claude-apt
```

```bash
# Full passwordless sudo (most convenient, least safe)
echo "$USER ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/claude-nopasswd && sudo chmod 0440 /etc/sudoers.d/claude-nopasswd
```

## Undo

```bash
sudo rm -f /etc/sudoers.d/claude-apt /etc/sudoers.d/claude-nopasswd
```

## Gotchas

- Passwordless sudo = anything running as this user can get root with no password. Fine for a throwaway lab VM, not for anything real or shared.
- Interactive `ssh`/`su` password prompts still hang; pass secrets as args or run those yourself.

## Related

- [[Home]]
