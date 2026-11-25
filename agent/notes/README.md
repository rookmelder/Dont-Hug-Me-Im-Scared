# Notes: measurements, benchmarks and history

The setup's memory. `CLAUDE.md` holds the rules; these notes hold what we **learned**. One entry per note.

## What goes in a note
- **Measurements**: tokens, time, calls and quality per worker/model, with the date and the task.
- **Lessons**: things that broke or surprised us, and the fix (e.g. "a role looped on the same command: added loop detection").
- **Model findings**: what worked, what failed (404, timeouts, loops, refusals). Update `MODELS.md` ratings to match.
- **Executor findings**: which allowlisted tools behaved, HexStrike quirks, commands that needed the lead's review first.

Not here: rules for the Lead or workers (`CLAUDE.md`, `agent/bases/`, `agent/roles/`), secrets, scan output or long logs
(summarise in a few lines, keep raw output in `.worker/`). Lessons about the *engagement* (not the setup) go in `knowledge/`.

## How to add an entry
- New note `agent/notes/YYYY-MM-DD-<topic>.md`: `# <Topic> (YYYY-MM-DD)`, then a one-line summary `> ...`,
  then `Back to [Notes](README.md).` Add one line for it at the bottom of the list below. Never append to an old note.
- Short and factual: numbers, model ids, what changed. One line per finding where possible. Mark untested claims.
- When a finding changes which model a role should use, also update `MODELS.md` and that role's `models:` line.

## Entries (oldest first)
<!-- This repo was forked from the Multi-Agent template and its history squashed; the template's own development
     notes were dropped. Add this fork's measurements and lessons below, one line each. -->
- (none yet)
