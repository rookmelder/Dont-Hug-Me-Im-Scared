# Models you have access to

Worker tools: **agy** (Google AI Pro) and **Codex** (ChatGPT plan) in `mode: full`; **Claude Code** (your Claude plan)
in `mode: claude` (PROJECT.md). The `models:` lines in `agent/roles/*.md`
use the first entries below. Model lists change over time — re-check before relying on one. Cost and limits: `LIMITS.md`.
What `delegate.py` actually reads (families, private_ok, default chains): `models.json`.

> **Not benchmarked in this fork.** The Multi-Agent template had a benchmark suite; it was removed here, so the picks
> below are starting points from each model's reputation and role, **not measured results**. Rate them on real
> engagement tasks and record what you find in `agent/notes/` — then adjust the chains here to match.

## The models
| Worker | Family | Use it for |
|---|---|---|
| `agy:gemini-3.8-flash-low` | gemini | Small builds, bulk content, docs: cheapest, fastest |
| `agy:gemini-3.8-flash-medium` | gemini | Reading a lot (summaries, scan triage); slower than low |
| `agy:claude-opus-4-6-thinking` | claude | The strongest agy thinker: research, security review, hard PoCs |
| `agy:claude-sonnet-4-6` | claude | Reviews and checks; also builds (exploit-builder fallback) |
| `agy:gpt-oss-120b-medium` | gpt | Checklist reviews only, last fallback |
| `codex:gpt-6-luna` | gpt | Fast GPT: tester, builder/scribe fallback |
| `codex:gpt-6.1-sol` | gpt | Coding and writing: exploit-builder, executor, cve-researcher |
| `codex:gpt-6-astra` | gpt | The strongest Codex thinker: research (`:high`), hardest PoCs, security review |
| `claude:opus` | claude | Claude mode: research, security review, hard PoCs (`:high` for research) |
| `claude:sonnet` | claude | Claude mode: builder, tester, executor, reviewer of Opus's work |
| `claude:haiku` | claude | Claude mode: scribe, recon-analyst, finding-scribe (cheap) |

In the model cache but not in the user's Codex picker (last checked 2026-11-17): `gpt-6.2-sol`, `gpt-6.2-astra` —
confirm the plan offers them before use. Legacy, not used: `gpt-6-sol`, `gpt-5.6-*`, `gpt-6.1-terra` (images, no role).

## Pick order per role
| Role | Base | #1 | #2 | #3 |
|---|---|---|---|---|
| Lead | - | Claude Opus (this session) | | |
| builder | builder | `agy:gemini-3.8-flash-low` | `codex:gpt-6-luna:low` | |
| tester | tester | `codex:gpt-6-astra:high` | `codex:gpt-6.1-sol:medium` | `agy:gemini-3.8-flash-medium` |
| reviewer | reviewer | `codex:gpt-6-astra:high` | `agy:claude-sonnet-4-6` | `agy:gpt-oss-120b-medium` |
| security-reviewer | reviewer | `codex:gpt-6-astra:high` | `agy:claude-opus-4-6-thinking` | `agy:claude-sonnet-4-6` |
| host-researcher | researcher | `codex:gpt-6-astra:high` | `agy:claude-opus-4-6-thinking` | `codex:gpt-6.1-sol:high` |
| recon-analyst | scribe | `agy:gemini-3.8-flash-low` | `codex:gpt-6-luna:low` | |
| cve-researcher | researcher | `codex:gpt-6-astra:high` | `agy:claude-opus-4-6-thinking` | `codex:gpt-6.1-sol:medium` |
| exploit-builder | builder | `codex:gpt-6-astra:high` | `agy:claude-opus-4-6-thinking` | `agy:claude-sonnet-4-6` |
| executor | executor | `codex:gpt-6.1-sol:medium` | `agy:gemini-3.8-flash-medium` | |
| report-scribe | scribe | `agy:gemini-3.8-flash-low` | `codex:gpt-6-luna:low` | |
| finding-scribe | scribe | `agy:gemini-3.8-flash-low` | `codex:gpt-6-luna:low` | |

Every chain ends with `claude:` entries (Opus for thinking roles, Sonnet for doing, Haiku for writing): those are the
workers in claude mode, and are skipped in full mode.

The idea: the cheapest model that should be good enough goes first. Checking roles need two families, because
`delegate.py --after` skips the family of the work they check (claude mode: the same model).

### Cyber routing notes
- **exploit-builder:** GPT models refuse exploit-style tasks more often, so the fallbacks are agy **Opus** and
  **Sonnet**, then Gemini. If all refuse, the Lead writes the PoC itself.
- **executor:** keep it on a trusted, non-refusing worker; it runs tools, so reliability matters more than coding
  strength. The Lead can also run HexStrike (or tools) directly instead of dispatching this role.
- **host-researcher / cve-researcher:** the researcher base has web access (Codex `web_search`, agy `search_web`,
  Claude WebSearch/WebFetch). Big thinking models on purpose: checking a CVE's version range against a distro
  backport is the hard part. They never get IPs or hostnames; `delegate.py` stops a leaking search.
- **recon-analyst:** summarises raw tool output the Lead pastes in; it runs nothing.

### Avoid (no role)
| Model | Where | Why |
|---|---|---|
| `gemini-3.8-flash-high` | agy | Overthinks: huge thinking budgets, long timeouts |

### Private (`private: yes` in PROJECT.md)
agy, Codex and Claude allowed (`private_ok` in `models.json`).
