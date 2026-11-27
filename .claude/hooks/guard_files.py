#!/usr/bin/env python3
"""PreToolUse hook (Write|Edit): never create AGENTS.md or GEMINI.md in this project.

agy and Codex load those files into every worker as extra rules, which would override the role rules
that delegate.py builds. Exit 2 blocks the tool call and shows stderr to Claude.
"""
import json
import sys
from pathlib import PurePath

BLOCKED = {'agents.md', 'gemini.md'}

try:
    data = json.loads(sys.stdin.buffer.read().decode('utf-8', 'replace'))   # Claude Code sends UTF-8, not the locale's code page
except ValueError:
    sys.exit(0)   # no usable input: don't block

name = PurePath(str((data.get('tool_input') or {}).get('file_path') or '').replace('\\', '/')).name
if name.lower() in BLOCKED:
    print(f"Blocked by .claude/hooks/guard_files.py: {name} is not allowed in this project. "
          "agy and Codex load it into every worker as rules. Put worker rules in agent/bases/, agent/roles/ "
          "or the Worker notes in PROJECT.md instead.", file=sys.stderr)
    sys.exit(2)
sys.exit(0)
