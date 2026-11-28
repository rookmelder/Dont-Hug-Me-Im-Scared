# Setting up the workers

You don't need everything. Each tool you add gives the Lead more workers. After adding anything, run
`python agent/check_setup.py`: it checks what you have and writes `SETUP.md`, and `delegate.py` then only uses
workers that work on your machine.

No API keys are needed. The worker tools work on Windows, Linux and macOS; **run the whole engagement on the
isolated Kali VM** (use `python3` where `python` is not on the PATH).

**Minimum that works:** Claude Code + git + Python + one worker tool (agy or Codex). Both is better: a tester or
reviewer must come from another model family than the builder. For live tool-running, add HexStrike (the Lead can
run it over MCP even with no worker tool).

| What | Gives you | Cost |
|---|---|---|
| Claude Code | The Lead (required) | Your Claude plan |
| git | Required (`delegate.py` uses `git status` to see what a worker changed) | Free |
| Python 3.8+ | Required: runs `agent/delegate.py`, `agent/check_setup.py` and the hooks (standard library only) | Free |
| agy (Google Antigravity CLI) | Gemini builders + the Claude Sonnet reviewer | Google AI Pro plan for real quota |
| Codex CLI (OpenAI) | GPT builders, testers, reviewers, executor | Your ChatGPT plan — see [codex.md](codex.md) |
| HexStrike (MCP) | Security tools (nmap, nuclei, ...) for the Lead and executor | Free (runs on the Kali VM) — see [hexstrike.md](hexstrike.md) |

## Claude Code (the Lead)
Install Claude Code and sign in with your Claude plan. Open this folder in it — Claude reads `CLAUDE.md` and takes
the Lead role. Nothing else to configure; it runs workers through `agent/delegate.py`.

## git
Install git (`sudo apt install git` / `brew install git` / git-scm.com), then set your identity once:
`git config --global user.name "..."` and `git config --global user.email "..."`. Optional, to push to GitHub:
install the `gh` CLI and `gh auth login`.

## agy (Google Antigravity CLI)
Gives you Gemini 3.8 Flash Low/Medium builders and the Claude Sonnet reviewer.
1. Install the Antigravity CLI (antigravity.google); check `agy` runs in a new terminal.
2. Sign in with the Google account that has **Google AI Pro** (without it the quota is tiny).
3. Check usage inside an agy chat with `/usage` (~20 worker jobs ≈ 6-7% of one 5-hour window).

This repo's `.agents/agents/` gives agy workers a trimmed tool set (only the executor worker gets a command tool).
Never put an `AGENTS.md` / `GEMINI.md` in the project: agy loads it into every worker as rules.

## Codex CLI and HexStrike
Codex has its own detailed guide including the sandbox and smoke tests: [codex.md](codex.md). HexStrike (the MCP
security-tool server for the Lead and the executor) has [hexstrike.md](hexstrike.md).

> **Worker command rule:** among workers only the `executor` base runs commands — the binaries in `PROJECT.md`
> `exec_allow` (agy gates these through its own global allowlist too) or the HexStrike tools over MCP. Every other
> worker is command-less. The Lead (Claude) may run tools directly; see `CLAUDE.md`.
