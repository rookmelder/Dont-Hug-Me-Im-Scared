#!/usr/bin/env python3
"""SessionStart hook: tell the Lead where the engagement stands, so CLAUDE.md doesn't have to.

Plain stdout with exit 0 is added to Claude's context. Prints nothing when everything is set up and authorised, so a
normal session costs zero extra tokens. Status only: it never prints targets, scope or findings.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _scope   # noqa: E402

root = Path(os.environ.get('CLAUDE_PROJECT_DIR') or '.')
facts = []
proj = _scope.read(root / 'PROJECT.md')
if not proj:
    facts.append('PROJECT.md is missing (cp PROJECT.example.md PROJECT.md).')
elif 'NOT FILLED IN YET' in proj:
    facts.append('PROJECT.md is not filled in yet.')
if not (root / 'SETUP.md').exists():
    facts.append('SETUP.md does not exist on this machine yet (python agent/check_setup.py writes it).')
state, names = _scope.status(root)
if state == 'none':
    facts.append('No engagement exists yet: use the new-engagement skill. Run nothing against any target until its SCOPE.md is authorised.')
elif state == 'unauthorised':
    facts.append('Engagement(s) ' + ', '.join(names) + ': SCOPE.md is NOT AUTHORISED YET. Run nothing and dispatch no executor task; ask the user to fill it in.')
elif state == 'ambiguous':
    facts.append('Several engagements exist (' + ', '.join(names) + '): confirm the active one with the user before anything runs.')
for n in names if state in ('ok', 'ambiguous') else []:
    if 'NOT WRITTEN YET' in _scope.read(root / 'engagements' / n / 'GOAL.md'):
        facts.append(f'engagements/{n}/GOAL.md is not written yet.')
if facts:
    print('Engagement status (from .claude/hooks/session_start.py): ' + ' '.join(facts))
