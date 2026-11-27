#!/usr/bin/env python3
"""PreToolUse hook (Bash): the project rules a shell command can break. Exit 2 blocks the call and shows stderr
to Claude; anything it can't parse passes.

Ported from the Multi-Agent template:
1. No AI attribution in `git commit` / `gh pr create|edit` messages, also in a `-F` / `--body-file` message file.
2. `delegate.py` runs need `--files`, except reviewer-base and executor roles (they change no project files).
3. No shell command may create AGENTS.md / GEMINI.md (guard_files.py covers Write/Edit).
Cyber additions:
4. Engagement data never reaches git: staged or `git add`-ed files under engagements/ (except README.md and
   _TEMPLATE/), PROJECT.md, GOAL.md, SCOPE.md block the commit / add.
5. Scope gate: `delegate.py --role executor` needs an authorised SCOPE.md (fail closed), and the Lead may not run
   offensive tools (nmap, sqlmap, hydra, ...) straight from Bash: only the executor or HexStrike (MCP, see
   guard_mcp.py) may. `--help` / `--version` pass.
6. No shell command may write SCOPE.md: authorisation is the user's to give, not the model's.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _scope   # noqa: E402

AT_COMMAND = r'(?:^|[;&|(\n{]|\$\()\s*(?:sudo\s+)?'   # where a command starts, so text that only mentions one doesn't count
GIT_COMMIT = re.compile(AT_COMMAND + r'git(?:\.exe)?(?:\s+-[cC]\s+\S+|\s+--?[\w-]+(?:=\S+)?)*\s+commit(?![\w-])', re.I | re.M)
GH_PR = re.compile(AT_COMMAND + r'gh(?:\.exe)?\s+pr\s+(?:create|edit)(?![\w-])', re.I | re.M)
ATTRIBUTION = re.compile(
    r'''(?:^|["'])[^\w\n]*(?:Co-Authored-By:[^\n]*(?:Claude|anthropic)|Generated with \[?Claude|Claude-Session:)''',
    re.I | re.M)
MESSAGE_FILE = re.compile(r'''(?:^|\s)(?:-F|--file|--body-file)(?:\s+|=)(?:"([^"]+)"|'([^']+)'|(\S+))''')
SEGMENT = re.compile(r'\n|;|&&|\|\||\|')
DELEGATE = re.compile(r'''\bpy(?:thon[\d.]*)?(?:\.exe)?["']?\s+(?:-\S+\s+)*["']?(?:\S*[\\/])?delegate\.py\b''', re.I)
BLOCKED_NAME = r'''(?:[^\s"';|&>]*[\\/])?(?:agents|gemini)\.md\b'''
REDIRECT_TO_BLOCKED = re.compile(r'''>{1,2}\s*["']?''' + BLOCKED_NAME, re.I)
WRITE_VERB = re.compile(r'^\s*(?:sudo\s+)?(?:git\s+)?(?:touch|tee|cp|mv|ln|install|New-Item|ni|Set-Content|Add-Content|'
                        r'Out-File|Copy-Item|cpi|copy|Move-Item|move|mi|Rename-Item|ren|rni)\b', re.I)
NAMES_BLOCKED = re.compile(r'''(?:^|[\s"'\\/=])(?:agents|gemini)\.md\b''', re.I)


OFFENSIVE = ('nmap', 'masscan', 'rustscan', 'nikto', 'sqlmap', 'hydra', 'medusa', 'patator', 'gobuster', 'feroxbuster',
             'ffuf', 'dirb', 'dirbuster', 'wfuzz', 'nuclei', 'msfconsole', 'msfvenom', 'responder', 'crackmapexec',
             'netexec', 'nxc', 'enum4linux', 'enum4linux-ng', 'wpscan', 'john', 'hashcat', 'searchsploit', 'impacket-\\w+')
OFFENSIVE_RE = re.compile(AT_COMMAND + r'(?:(?:\S*/)?(?:' + '|'.join(OFFENSIVE) + r'))(?![\w.-])', re.I)
SCOPE_NAME = r'''(?:[^\s"';|&>]*[\\/])?SCOPE\.md\b'''
REDIRECT_TO_SCOPE = re.compile(r'''>{1,2}\s*["']?''' + SCOPE_NAME, re.I)
SCOPE_WRITE_VERB = re.compile(r'^\s*(?:sudo\s+)?(?:touch|tee|cp|mv|ln|install|dd|truncate|sed\s+(?:-\w*i\w*|--in-place)|perl\s+-\w*i|'
                              r'python3?\s+-c|Set-Content|Add-Content|Out-File)\b', re.I)
NAMES_SCOPE = re.compile(r'(?:^|[\s"\'\\/=])SCOPE\.md\b', re.I)
PRIVATE_PATH = re.compile(r'''(?:^|[\s"'=])(?:\./)?(?:engagements/(?!README\.md\b|_TEMPLATE\b)\S+|(?:PROJECT|GOAL|SCOPE)\.md\b)''')
GIT_ADD = re.compile(AT_COMMAND + r'git(?:\.exe)?(?:\s+-[cC]\s+\S+|\s+--?[\w-]+(?:=\S+)?)*\s+add(?![\w-])', re.I | re.M)
EXECUTOR_ROLE = re.compile(r'''--role(?:\s+|=)["']?executor\b''')


def block(msg):
    print('Blocked by .claude/hooks/guard_shell.py: ' + msg, file=sys.stderr)
    sys.exit(2)


def message_files(cmd, cwd):
    """Text of each message file the command names (missing or unreadable files are skipped)."""
    texts = []
    for m in MESSAGE_FILE.finditer(cmd):
        name = next(g for g in m.groups() if g)
        if name == '-':
            continue
        path = Path(name) if Path(name).is_absolute() else Path(cwd) / name
        try:
            texts.append(path.read_text(encoding='utf-8-sig', errors='replace'))
        except OSError:
            pass
    return texts


def check_attribution(cmd, cwd):
    if any(ATTRIBUTION.search(text) for text in [cmd] + message_files(cmd, cwd)):
        block("this project's commits and PRs carry no AI attribution (no Co-Authored-By: Claude, "
              "no 'Generated with Claude Code', no Claude-Session). Run the command again without those lines.")


def role_base(root, role):
    try:
        text = (root / 'agent' / 'roles' / f'{role}.md').read_text(encoding='utf-8-sig')
    except OSError:
        return ''
    m = re.search(r'^base:\s*(\w+)', text, re.M)
    return m.group(1).lower() if m else 'builder'


def check_engagement_files(root, cmd, staged_too):
    """Engagement data, PROJECT.md, GOAL.md, SCOPE.md must never be staged or committed (this repo is public)."""
    if any(GIT_ADD.search(s) and PRIVATE_PATH.search(s) for s in SEGMENT.split(cmd)):
        block('engagements/ data, PROJECT.md, GOAL.md and SCOPE.md never go into git (public repo, real targets). '
              'Do not `git add` them, not even with -f.')
    if not staged_too:
        return
    try:
        r = subprocess.run(['git', 'diff', '--cached', '--name-only'], cwd=str(root), capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return
    bad = [f for f in r.stdout.splitlines()
           if (f.startswith('engagements/') and f != 'engagements/README.md' and not f.startswith('engagements/_TEMPLATE/'))
           or f in ('PROJECT.md', 'GOAL.md', 'SCOPE.md')]
    if bad:
        block('staged files that must stay out of git (engagement data / real targets): ' + ', '.join(bad[:10])
              + '. Run `git reset -q -- <file>` on them, fix the ignore rule, then commit.')


def check_scope_gate(seg, root):
    """Executor runs need an authorised SCOPE.md; the Lead never runs offensive tools straight from Bash."""
    if DELEGATE.search(seg) and EXECUTOR_ROLE.search(seg) and not re.search(r'(?:^|\s)(?:-h|--help)\b', seg):
        state, names = _scope.status(root)
        if state in ('none', 'unauthorised'):
            block('no engagement has an authorised SCOPE.md (state: ' + state + '). Ask the user to fill in '
                  'engagements/<name>/SCOPE.md first; no executor task runs while it says NOT AUTHORISED YET.')
        if state == 'ambiguous':
            block('several engagements exist (' + ', '.join(names) + '): confirm the active one with the user, then '
                  'keep only that one under engagements/ authorised, or move the others away.')
        bad = _scope.out_of_scope(root, seg)
        if bad:
            block('target(s) not in the authorised SCOPE.md: ' + ', '.join(bad[:8]) + '. Add them to SCOPE.md (the user '
                  'does that) before any run.')
        return
    if OFFENSIVE_RE.search(seg) and not re.search(r'(?:^|\s)(?:-h|--help|--version|-V)(?:\s|$)', seg):
        block('the Lead does not run offensive tools straight from Bash (CLAUDE.md). Dispatch the executor '
              '(delegate.py --role executor, with the target from SCOPE.md in the task) or use HexStrike over MCP.')


def check_scope_write(seg):
    if REDIRECT_TO_SCOPE.search(seg) or (SCOPE_WRITE_VERB.search(seg) and NAMES_SCOPE.search(seg)):
        block('SCOPE.md is the user\'s authorisation: only the user may change it. Ask them to edit '
              'engagements/<name>/SCOPE.md and carry on once they have.')


def check_delegate(seg, root):
    if not DELEGATE.search(seg) or re.search(r'(?:^|\s)(?:-h|--help)\b', seg):
        return
    if re.search(r'(?:^|\s)--files(?:\s|=)', seg):
        return
    m = re.search(r'''--role(?:\s+|=)["']?([\w.-]+)''', seg)
    if m and (role_base(root, m.group(1)) in ('reviewer', 'executor') or m.group(1) == 'executor'):
        return
    block('give delegate.py --files <what the worker may change> (CLAUDE.md: always give it). Without it the '
          "summary can't flag changes outside the task and delegate.py can't stop two workers on the same files. "
          'Only reviewer-base and executor roles may leave it out.')


def check_blocked_names(seg):
    if REDIRECT_TO_BLOCKED.search(seg) or (WRITE_VERB.search(seg) and NAMES_BLOCKED.search(seg)):
        block('AGENTS.md / GEMINI.md are not allowed in this project: agy and Codex load them into every worker as '
              'rules. Put worker rules in agent/bases/, agent/roles/ or the Worker notes in PROJECT.md instead.')


def main():
    try:
        data = json.loads(sys.stdin.buffer.read().decode('utf-8', 'replace'))   # Claude Code sends UTF-8
    except ValueError:
        return 0   # no usable input: don't block
    cmd = str((data.get('tool_input') or {}).get('command') or '')
    cwd = data.get('cwd') or '.'
    root = Path(os.environ.get('CLAUDE_PROJECT_DIR') or cwd)
    commit, pr = GIT_COMMIT.search(cmd), GH_PR.search(cmd)
    if commit or pr:
        check_attribution(cmd, cwd)
        if commit:
            check_engagement_files(root, cmd, True)
        return 0
    check_engagement_files(root, cmd, False)   # a commit or PR message may mention anything: skip the checks on its text below
    for seg in SEGMENT.split(cmd):
        check_delegate(seg, root)
        check_scope_gate(seg, root)
        check_scope_write(seg)
        check_blocked_names(seg)
    return 0


if __name__ == '__main__':
    sys.exit(main())
