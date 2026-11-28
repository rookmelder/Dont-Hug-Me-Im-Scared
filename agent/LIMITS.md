# Worker tools: cost, limits, quirks

Status 2026-11-17. Plans and limits change: re-check before relying on a number.
Which model to pick per role: `MODELS.md`. What `delegate.py` knows: `models.json`.

| Tool | What you pay | Limits | Watch out |
|---|---|---|---|
| **Claude** (Lead) | Your Claude plan | Plan limits | The expensive brain: keep it for planning and review |
| **agy** (Google AI Pro) | Pro subscription | Pro quota for Gemini, separate pool for Claude/gpt-oss; every 5 h + weekly cap | ~20 worker runs ≈ 6-7% of a 5 h window. Check with `/usage` in agy |
| **Claude workers** (claude mode) | Your Claude plan | The same 5-hour / weekly windows as the Lead | Every worker run uses the Lead's own limits: keep Haiku for cheap roles. A limit hit shows as exit 6 (RATE LIMITED in the live log) |
| **Codex** (ChatGPT plan) | Your ChatGPT plan | The plan's Codex usage limits (shared with your own Codex use) | Not measured in this setup yet. A limit hit shows as exit 6: the next worker in the chain takes over |

**Privacy:** no free tiers that train on prompts are used any more.

## Notes per tool
- **agy**: workers run through a role agent with only the tools that role needs (~3.6k tokens per call instead of
  ~10.4k), with per-file deny rules for the project's secret files (tested 2026-11-17: a read of `.env` was denied).
- **Claude** (claude mode): `claude -p --safe-mode --restricted` (no CLAUDE.md, hooks or project settings), only the
  base's tools, `dontAsk` permissions, per-file deny rules for secrets. Tested 2026-11-28: it could not see CLAUDE.md,
  wrote files when allowed, and a researcher ran web searches and returned the schema JSON.
- **Codex**: `codex exec` with your config ignored, no shell, no web (researchers: live web search), no subagents, and a permission profile (see
  `setup/codex.md`). The model list your plan offers changes; `~/.codex/models_cache.json` has the current one.
