# Models you have access to

Status 2026-11-17 (ratings carried over from the Multi-Agent template). Two worker tools: **agy** (Google AI Pro)
and **Codex** (ChatGPT plan). The `models:` lines in `agent/roles/*.md` use the first entries below. Lists change: re-check.

**Priority** = pick order within a role: #1 first; the next one when #1 is busy, out of quota, or the same model
family as the work a tester/reviewer checks (`delegate.py --after`). **Rating** = quality as a worker, out of 10.
**Basis**: **T** = tested on the template's benchmark, **R** = reputation / the model's own description, **U** = not
run yet in this setup. The template's benchmark suite was removed in this cyber fork, so the T ratings below are
carried over, not re-run here; record new measurements in `agent/notes/`. Cost and limits: `LIMITS.md`.

## The models
| Worker | Family | Use it for | Basis |
|---|---|---|---|
| `agy:gemini-3.8-flash-low` | gemini | Small builds, bulk content, docs: cheapest, fastest | T (22/22 easy; 58/68 harder sk_* bench: misses subtle review bugs, 13/20 as tester) |
| `agy:gemini-3.8-flash-medium` | gemini | Reading a lot (summaries, scan triage) | T (62/68 harder sk_* bench, 17/20 as tester; 3-9x slower than low) |
| `agy:claude-sonnet-4-6` | claude | Every checking role: reviewer, security, safety, fact-check | T (fewest false findings) |
| `agy:gpt-oss-120b-medium` | gpt | Checklist reviews only, last fallback | T (makes things up otherwise) |
| `codex:gpt-6-luna` | gpt | Fast GPT: tester, builder/scribe fallback | R, U |
| `codex:gpt-6.1-sol` | gpt | Coding and writing: exploit-builder, executor, cve-researcher | R, U |
| `codex:gpt-6-astra` | gpt | Complex coding and reasoning: hardest pieces, security fallback | R, U |
| `codex:gpt-6.1-terra` | gpt | Images (no cyber role uses it yet; kept for reference) | R, U |

In the model cache but not in the user's Codex picker (2026-11-17): `gpt-6.2-sol`, `gpt-6.2-astra`. Check that the
plan offers them before using them. Legacy, not used: `gpt-6-sol`, `gpt-5.6-*`.

## Pick order per role
| Role | Base | #1 | #2 | #3 |
|---|---|---|---|---|
| Lead | - | Claude Opus 5.5 (T) | | |
| builder | builder | `agy:gemini-3.8-flash-low` | `codex:gpt-6-luna:low` | |
| tester | tester | `codex:gpt-6-astra:high` | `codex:gpt-6.1-sol:medium` | `agy:gemini-3.8-flash-medium` |
| reviewer | reviewer | `codex:gpt-6-astra:high` | `agy:claude-sonnet-4-6` | `agy:gpt-oss-120b-medium` |
| security-reviewer | reviewer | `codex:gpt-6-astra:high` | `agy:claude-sonnet-4-6` | |
| recon-analyst (cyber) | scribe | `agy:gemini-3.8-flash-low` | `codex:gpt-6-luna:low` | |
| cve-researcher (cyber) | reviewer | `codex:gpt-6.1-sol:medium` | `agy:claude-sonnet-4-6` | |
| exploit-builder (cyber) | builder | `codex:gpt-6.1-sol:medium` | `agy:gemini-3.8-flash-medium` | |
| executor (cyber) | executor | `codex:gpt-6.1-sol:medium` | `agy:gemini-3.8-flash-medium` | |
| report-scribe (cyber) | scribe | `agy:gemini-3.8-flash-low` | `codex:gpt-6-luna:low` | |

Why: the cheapest model that should be good enough goes first. Checking roles have two families, because the script
skips the family of the work they check. Claude Sonnet is for checking roles only (separate agy pool). These cyber
chains are **not benchmarked yet** (basis R/U): rate them on real engagement tasks and record findings in `agent/notes/`.

### Cyber routing notes
- **exploit-builder:** GPT models refuse exploit-style tasks more often than others, so the fallback is **Gemini**
  (agy), not another GPT. If both refuse, the Lead (Claude) writes the PoC itself — Claude Sonnet is reviewer-only as
  an agy worker, so it is not in the builder chain. Watch for refusals and note them.
- **executor:** keep it on a trusted, non-refusing worker; it runs tools, so coding strength matters less than
  reliability. The Lead can also run HexStrike directly over MCP instead of dispatching this role.
- **cve-researcher:** it does NOT look CVEs up (workers have no web access, and model CVE memory is stale). The Lead
  does the web/HexStrike lookup and pastes the raw CVE data in; the worker ranks and triages it against the target.
- **recon-analyst:** summarises raw tool output the Lead pastes in; it runs nothing.

### Private (`private: yes` in PROJECT.md)
agy and Codex both allowed (`private_ok` in `models.json`), with "Improve the model for everyone" OFF in ChatGPT.

### Avoid (no role)
| Model | Where | Why |
|---|---|---|
| `gemini-3.8-flash-high` | agy | Overthinks: 50k+ thinking tokens, 9 min timeouts |
| `claude-opus-4-6-thinking` | agy | Duplicates the Lead and burns the agy pool |

Removed 2026-11-17: the API workers (NVIDIA, Gemini API, OpenRouter, OpenAI through Copilot CLI). Their measurements
stay in `agent/notes/`.
