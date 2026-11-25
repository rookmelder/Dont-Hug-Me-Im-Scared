# HexStrike (MCP server for security tooling)

HexStrike exposes security tools (nmap, nuclei, and many more) to an AI agent over **MCP**. The Lead (Claude Code)
connects to it and can also run tools through it; the `executor` worker can be given the same MCP access. It runs on
the **isolated Kali VM only** — never expose it off the lab network.

> Versions move fast: treat the exact flags/paths below as the shape, and confirm against HexStrike's own README for
> the version you install. The invariants that matter (localhost only, lab network only, authorised targets only) do not change.

## 1. Install and start the server (on Kali)
1. Install HexStrike per its README (clone the repo, install its Python requirements in a venv, have the underlying
   tools — nmap etc. — on `PATH`).
2. Start the MCP server bound to localhost:
   ```bash
   # from the HexStrike repo, in its venv — confirm the real entrypoint in its README
   python3 hexstrike_server.py --host 127.0.0.1 --port 8888
   ```
3. Confirm it is up and local only:
   ```bash
   curl -s http://127.0.0.1:8888/health   # or the health path its README documents
   ss -ltnp | grep 8888                    # should be bound to 127.0.0.1, not 0.0.0.0
   ```

## 2. Connect the Lead (Claude Code) over MCP
Add HexStrike as an MCP server for this project, e.g.:
```bash
claude mcp add hexstrike -- python3 /path/to/hexstrike/hexstrike_mcp.py --server http://127.0.0.1:8888
```
(or the stdio/HTTP form its README gives). Then `/mcp` in Claude Code should list the HexStrike tools. The Lead can
now run tools directly — the simplest path for enumeration you watch live.

## 3. (Optional) give the executor worker MCP access
`delegate.py` runs Codex workers with `--ignore-user-config`, which strips MCP servers, so the Codex executor does
**not** reach HexStrike; it runs the `exec_allow` binaries directly instead. To route HexStrike through the executor,
use an **agy** executor worker and add the HexStrike MCP server to that worker's config (`.agents/agents/w-executor.md`
/ agy MCP settings), per agy's MCP docs. Validate on the lab VM before trusting it.

## 4. Safety wiring (do this before the first run)
- **SCOPE.md** lists the only targets any tool may touch. HexStrike does not read it — you (the Lead) and the
  executor base enforce scope. Never pass a tool a target that is not in `SCOPE.md`.
- **exec_allow** in `PROJECT.md` lists the binaries the executor may run outside MCP. Keep it tight (start with `nmap`).
- **agy global allowlist**: an agy executor only runs commands agy's global settings permit — add exactly the
  `exec_allow` binaries there and nothing else (see `agy.md`).
- Nothing leaves the VM: no results, no loot, no telemetry to the internet.
