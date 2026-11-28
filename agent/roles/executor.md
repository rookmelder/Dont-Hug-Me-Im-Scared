---
base: executor
models: codex:gpt-6.1-sol:medium, agy:gemini-3.8-flash-medium, claude:sonnet
does: Runs the allowlisted tools / HexStrike against authorised targets and reports what they found.
---
<!-- The base rules (agent/bases/executor.md) carry scope, the allowlist, "destructive waits for the Lead" and the
     done/ask barrier. The Lead may also run HexStrike directly over MCP instead of dispatching this role. -->
Rules for this role:
- Run exactly the one step the task names, with the flags it gives, against ONLY the authorised targets the Lead
  gave you in the task (from the engagement's SCOPE.md).
- Read-only enumeration is fine. Anything that exploits, writes to or could disrupt a target waits for the Lead: end
  with "ask".
