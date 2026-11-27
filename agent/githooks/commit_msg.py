#!/usr/bin/env python3
"""Run by agent/githooks/commit-msg: refuse a commit message with an AI attribution line.

The pre-commit hook next to it refuses staged engagement data (same rule as .claude/hooks/guard_shell.py).

Uses the same pattern as the Claude Code hook (.claude/hooks/guard_shell.py), so both stay in step.
Comment lines (#) are ignored, as git drops them. Exit 1 stops the commit.
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def attribution_pattern():
    spec = importlib.util.spec_from_file_location('guard_shell', ROOT / '.claude' / 'hooks' / 'guard_shell.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.ATTRIBUTION


def main(argv):
    if len(argv) < 2:
        return 0
    try:
        text = Path(argv[1]).read_text(encoding='utf-8-sig', errors='replace')
        pattern = attribution_pattern()
    except (OSError, ImportError, AttributeError) as e:
        print(f'commit-msg hook: check skipped ({e})', file=sys.stderr)
        return 0
    text = '\n'.join(l for l in text.splitlines() if not l.startswith('#'))
    m = pattern.search(text)
    if m:
        line = text[m.start():].lstrip('"\'').splitlines()[0].strip()
        print(f'commit-msg hook (agent/githooks): this project\'s commits carry no AI attribution. Remove this line '
              f'and commit again:\n  {line}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
