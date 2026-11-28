#!/usr/bin/env python3
"""PreToolUse hook (mcp__hexstrike*): HexStrike tools run real security tools, and HexStrike itself never reads
SCOPE.md. This hook does: fail closed while no engagement is authorised, and block any host/IP in the tool input that
the authorised SCOPE.md does not list. Exit 2 blocks the call and shows stderr to Claude.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _scope   # noqa: E402


def block(msg):
    print('Blocked by .claude/hooks/guard_mcp.py: ' + msg, file=sys.stderr)
    sys.exit(2)


def main():
    try:
        data = json.loads(sys.stdin.buffer.read().decode('utf-8', 'replace'))
    except ValueError:
        return 0
    root = Path(os.environ.get('CLAUDE_PROJECT_DIR') or data.get('cwd') or '.')
    state, names = _scope.status(root)
    if state in ('none', 'unauthorised'):
        block('no engagement has an authorised SCOPE.md. Ask the user to fill in engagements/<name>/SCOPE.md; no '
              'HexStrike tool runs while it says NOT AUTHORISED YET.')
    if state == 'ambiguous':
        block('several engagements exist (' + ', '.join(names) + '): confirm which is active with the user first.')
    bad = _scope.out_of_scope(root, json.dumps(data.get('tool_input') or {}))
    if bad:
        block('target(s) not in the authorised SCOPE.md: ' + ', '.join(bad[:8]) + '. Only the user adds targets to SCOPE.md.')
    lvl = _scope.level(root)
    if lvl < 4:
        name = data.get('tool_name') or ''
        req = _scope.mcp_required_level(name)
        if req and req > lvl:
            block('HexStrike ' + name + ' needs level ' + str(req) + ' (' + _scope.level_name(req) + '); this engagement '
                  'is level ' + str(lvl) + ' (' + _scope.level_name(lvl) + '). Raise the level in SCOPE.md to use it.')
        hit = _scope.destructive_hit(name + ' ' + json.dumps(data.get('tool_input') or {}))
        if hit:
            block('DoS / destructive HexStrike use (matched ' + hit + ') runs only at level 4 (god-mode); this '
                  'engagement is level ' + str(lvl) + '.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
