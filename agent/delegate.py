#!/usr/bin/env python3
"""Send one task to a worker (agy or Codex) by role, with safe defaults.

Examples (from the project root; Windows, Linux and macOS):
  python agent/delegate.py --role builder --task-file .worker/t1.md --include src/shop.py
  python agent/delegate.py --role reviewer --after 3fa2b1c0 --task-file .worker/review.md
  python agent/delegate.py --role builder --worker codex:gpt-6.1-sol:medium --task-file .worker/t1.md   # force one worker

Roles: any agent/roles/<name>.md (frontmatter: base, models). Core rules per base: agent/bases/<base>.md.
Each role has a worker chain (agy:<model> or codex:<model>[:<effort>]); workers missing on this machine (SETUP.md)
are skipped. On a busy/quota error it retries once when the wait is short, then moves on. --model / --worker force one.
Models, families and harness rules live in agent/models.json.
Every base but executor runs no commands. The executor base runs an allowlist of tools (exec_allow in PROJECT.md):
every program in a command must be on it (each part of a pipe/list, inside bash -c, past sudo/env/timeout; $(...) and
backticks are refused). Commands are read live from the worker's output (Codex and agy) and checked as they start:
an off-allowlist command, a loop or going over --max-commands stops the worker at once (exit 4 for a breach).
For builder/tester roles this script runs check_one itself after the worker is done
(--part fills {name}); when it fails, the worker gets the output to fix it, then the check runs again
(a second round only if the first one changed the failure).
For reviewer roles the check runs first and its result is pasted into the task.
Tester and reviewer roles need --after <builder run id> (or --after lead): they never run on the builder's model family.
Paths: --include and --files must stay inside the project and never name a secret (.env, keys, credentials);
workers are denied reading or writing the secret files this script finds in the project.
--files names what the task may change: with workers in parallel, each run then reports only its own files.
Output: a short summary (full JSON saved in .worker/run-<id>.json and .worker/last.json); --json prints the JSON instead.
Live view (always on): `tail -f .worker/live.log` shows every worker as it works; .worker/run-<id>.log keeps each
run's prompts and full raw output (every command's output included).
Exit: 0 ok, 2 bad input, 3 timeout (check git status: files often exist), 4 blocked, 5 empty, 6 worker error,
7 check failed.
Project settings (check commands, worker notes) come from PROJECT.md. Standard library only.
"""
import argparse
import fnmatch
import hashlib
import ipaddress
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parent      # agent/: this script, bases/, roles/
ROOT = AGENT_DIR.parent                           # project root: workers work here
IS_WIN = os.name == 'nt'

CONFIG = json.loads((AGENT_DIR / 'models.json').read_text(encoding='utf-8-sig'))   # models, families: edit that file
_plain = lambda d: {k: v for k, v in d.items() if not k.startswith('_')}
AGY_MODELS = CONFIG['agy_models']
CODEX_EFFORTS = CONFIG['codex_efforts']
FAMILIES = _plain(CONFIG['families'])                  # model id prefix -> family
PRIVATE_OK = CONFIG['private_ok']                      # harnesses a private project may use
HARNESSES = ('agy', 'codex', 'claude')
MODE_HARNESSES = {'full': ('agy', 'codex'), 'claude': ('claude',)}   # PROJECT.md mode: which harnesses workers use
BASES = ('builder', 'tester', 'reviewer', 'scribe', 'executor', 'researcher')
COMMANDLESS = ('builder', 'tester', 'reviewer', 'scribe', 'researcher')   # invariant: only the executor base may run commands
WEB_BASES = ('researcher',)   # the only bases with web search / fetch
CLAUDE_EFFORTS = tuple(CONFIG.get('claude_efforts') or ('low', 'medium', 'high', 'xhigh', 'max'))
MAX_WORKERS = {'agy': 3, 'codex': 2, 'claude': 3}   # default worker cap per harness (PROJECT.md max_agy / max_codex / max_claude)
DEFAULT_MODELS = _plain(CONFIG['default_models'])      # used when a role file has no models: line
TRANSIENT = re.compile(r'429|503|UNAVAILABLE|RESOURCE_EXHAUSTED|capacity|rate limit|overloaded|timed out', re.I)
LABELS = {0: 'OK', 3: 'TIMEOUT (check git status)', 4: 'BLOCKED', 5: 'EMPTY', 6: 'WORKER ERROR', 7: 'CHECK FAILED'}
MAX_RETRY_WAIT = 120   # a worker asking for a longer wait: go to the next worker instead
CHECK_TAIL_LINES, CHECK_TAIL_CHARS = 60, 6000   # how much check output a worker / the summary gets
EXEC_MAX_COMMANDS = 100   # executor command budget per run (PentAGI caps workers ~100); --max-commands overrides
EXEC_LOOP_REPEAT = 3      # the same command this many times in one run = looping: stop so the Lead changes tack

# Secret files: never pasted in, never in --files, denied to every worker.
SECRET_NAME = re.compile(r'^(\.env(\.(?!(example|sample|template|dist)$)[^/]+)?|\.netrc|\.git-credentials|\.npmrc|\.pypirc'
                         r'|id_(rsa|dsa|ecdsa|ed25519)(\.pub)?|credentials(\.json)?|.+\.(pem|key|p12|pfx|jks|keystore))$', re.I)
SECRET_GLOBS = ['**/.env', '**/.env.*', '**/*.pem', '**/*.key', '**/*.p12', '**/*.pfx', '**/id_rsa*', '**/id_ed25519*',
                '**/.netrc', '**/.git-credentials', '**/credentials.json']   # Codex deny-read patterns (on top of the files found)
SKIP_DIRS = {'.git', 'node_modules', '.venv', 'venv', '__pycache__', '.worker', '.mypy_cache', '.pytest_cache'}


class Fail(Exception):
    def __init__(self, msg, code):
        super().__init__(msg)
        self.code = code


def read_text(path):
    return Path(path).read_text(encoding='utf-8-sig')


# --- Files the scripts read ----------------------------------------------------------------
def parse_project(text):
    """PROJECT.md: the ```settings block, the '## Worker notes' section and the Private flag."""
    proj = {'check_one': '', 'check_all': '', 'check_dir': '', 'private': '', 'exec_allow': '', 'mode': 'full',
            'max_agy': '', 'max_codex': '', 'max_claude': ''}
    m = re.search(r'```settings\s*\r?\n(.*?)```', text, re.S)
    if m:
        for line in re.split(r'\r?\n', m.group(1)):
            lm = re.match(r'^\s*(\w+)\s*:\s*(.*?)\s*$', line)
            if lm:
                proj[lm.group(1)] = lm.group(2).strip('`')
    notes = ''
    m = re.search(r'## Worker notes[^\n]*\n(.*?)(?=\n## |\Z)', text, re.S)
    if m:
        notes = m.group(1).strip()
    if notes.startswith('- <'):   # template placeholder, not filled in
        notes = ''
    # Private = only the harnesses in models.json private_ok. Anything but a clear "no" counts as private.
    val = proj.get('private', '').lower()
    if val in ('yes', 'no'):
        private = val == 'yes'
    else:   # older PROJECT.md: the "**Private?** yes/no" line under About
        old = re.search(r'\*\*Private\?\*\*\s*(yes|no)\b', text)
        private = not (old and old.group(1) == 'no')
    return proj, notes, private


def parse_role(text):
    """Role file = frontmatter (base, models, does) + extra instructions. Returns (fields, body)."""
    m = re.match(r'^---\s*\r?\n(.*?)\r?\n---\s*\r?\n?(.*)$', text, re.S)
    if not m:
        return {}, text
    fm = {}
    for line in re.split(r'\r?\n', m.group(1)):
        lm = re.match(r'^\s*(\w+)\s*:\s*(.*?)\s*$', line)
        if lm:
            fm[lm.group(1)] = lm.group(2)
    return fm, m.group(2).strip()


def to_worker(s):
    """'agy:gemini-3.8-flash-low' | 'codex:gpt-6.1-sol' | 'codex:gpt-6-luna:low' -> {'h', 'm', 'e'}"""
    head, _, rest = s.strip().partition(':')
    model, _, effort = rest.partition(':')
    if head not in HARNESSES or not model:
        raise Fail(f"Worker '{s.strip()}': write agy:<model>, codex:<model>[:<effort>] or claude:<model>[:<effort>].", 2)
    if head == 'agy' and effort:
        raise Fail(f"Worker '{s.strip()}': agy models have no :<effort> (pick another agy model instead).", 2)
    efforts = CLAUDE_EFFORTS if head == 'claude' else CODEX_EFFORTS
    if effort and effort not in efforts:
        raise Fail(f"Worker '{s.strip()}': effort must be one of {', '.join(efforts)}.", 2)
    return {'h': head, 'm': model, 'e': effort}


def parse_chain(models):
    return [to_worker(x) for x in models.split(',') if x.strip()]


def worker_name(w):
    return f"{w['h']} {w['m']}" + (f" ({w['e']})" if w.get('e') else '')


def family(model):
    """Model id -> family (models.json families), so a tester/reviewer never checks its own family's work."""
    for prefix, fam in FAMILIES.items():
        if (model or '').startswith(prefix):
            return fam
    return model or ''


def parse_available(text):
    """SETUP.md ```available block -> {'agy': True, ...}, or None when there is no block."""
    m = re.search(r'```available\s*\r?\n(.*?)```', text, re.S)
    if not m:
        return None
    out = {}
    for line in re.split(r'\r?\n', m.group(1)):
        lm = re.match(r'^\s*(\w+)\s*:\s*(yes|no)', line)
        if lm:
            out[lm.group(1)] = lm.group(2) == 'yes'
    return out


def is_available(w, available):
    return available is None or bool(available.get(w['h']))


# --- Paths: inside the project, never a secret ---------------------------------------------
def is_secret(path):
    return bool(SECRET_NAME.match(str(path).replace('\\', '/').rstrip('/').rsplit('/', 1)[-1]))


def project_path(p, what):
    """A path or glob the Lead gave (--include, --files) -> relative to the project root, with / slashes.
    Refused (exit 4): outside the project, inside .git/, or a secret file."""
    raw = str(p).strip()
    full = raw if os.path.isabs(raw) else os.path.join(str(ROOT), raw)
    try:
        rel = os.path.relpath(os.path.realpath(full), os.path.realpath(str(ROOT))).replace('\\', '/')
    except ValueError:   # another drive (Windows)
        rel = '../'
    if rel == '..' or rel.startswith('../') or os.path.isabs(rel):
        raise Fail(f"{what} '{raw}': outside the project folder. Workers only get files from the project.", 4)
    if rel.split('/')[0] == '.git':
        raise Fail(f"{what} '{raw}': inside .git/.", 4)
    if is_secret(rel):
        raise Fail(f"{what} '{raw}': a secret file (.env, keys, credentials) never goes to a worker.", 4)
    return rel


def secret_files(root):
    """Absolute paths of the secret files in the project (what workers are denied), skipping .git and caches."""
    out = []
    for d, dirs, files in os.walk(str(root)):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        out += [os.path.join(d, f) for f in files if is_secret(f)]
    return sorted(out)


def check_command(check_one, part):
    """check_one with {name} filled in -> (command, ''), or (None, why it can't run)."""
    cmd = (check_one or '').strip()
    if not cmd:
        return None, 'no check command in PROJECT.md'
    if '{name}' in cmd:
        if not part:
            return None, 'give --part <name> to fill {name} in check_one'
        cmd = cmd.replace('{name}', part)
    return cmd, ''


def check_text(check):
    """A check result as text for a worker or the summary."""
    if check.get('skipped'):
        return f"not run ({check['skipped']})"
    head = 'PASS' if check['passed'] else ('FAIL: timed out' if check['timed_out'] else f"FAIL (exit {check['exit']})")
    return f"{head} | `{check['cmd']}`"


def failure_key(check):
    """The check output without what changes on every run (timings, addresses): equal keys = no progress."""
    out = re.sub(r'\d+(\.\d+)?\s*(s|ms|sec|seconds)\b', '', check.get('output') or '')
    return re.sub(r'0x[0-9a-fA-F]+', '', out).strip()


# --- Executor base: the one base that may run commands (allowlist, budget, loop detection) --------
def parse_allow(spec):
    """exec_allow from PROJECT.md -> the set of command binaries an executor may run (names only, no paths)."""
    return {Path(x).name for x in re.split(r'[\s,]+', (spec or '').strip()) if x}


def command_binary(cmd):
    """The program a shell command runs, for the allowlist: the first bare word past env VAR=... and wrappers.
    'VAR=1 sudo /usr/bin/nmap -sV x' -> 'nmap'. Best-effort; the harness allowlist and SCOPE.md are the real gates."""
    if isinstance(cmd, (list, tuple)):
        cmd = ' '.join(str(c) for c in cmd)
    for t in str(cmd or '').strip().split():
        if re.match(r'^[A-Za-z_]\w*=', t):      # leading ENV=val assignment
            continue
        if t in ('sudo', 'env', 'command', 'nice', 'nohup', 'time'):
            continue                            # common wrappers: look at the next word
        return Path(t.strip('"\'')).name
    return ''


SHELLS = {'sh', 'bash', 'dash', 'zsh', 'ksh'}
# Wrappers that run the next word as the program, with their options that take an argument (skipped with it).
WRAPPERS = {'sudo': {'-u', '-g', '-C', '-D', '-h', '-p', '-U', '-r', '-t', '-T', '--user', '--group', '--prompt'},
            'doas': {'-u', '-C'}, 'env': {'-u', '-C', '-S', '--unset', '--chdir', '--split-string'},
            'nice': {'-n', '--adjustment'}, 'stdbuf': {'-i', '-o', '-e'}, 'timeout': {'-s', '-k', '--signal', '--kill-after'},
            'command': set(), 'nohup': set(), 'time': {'-f', '-o'}}
SHELL_WORDS = {'!', '{', '}', 'then', 'do', 'else', 'fi', 'done'}   # skipped at a command start; any other keyword fails
SEPARATORS = {';', '&', '&&', '|', '||', '|&', '(', ')', ';;'}
REDIRECTS = {'<', '>', '>>', '<<', '<<<', '>&', '&>', '&>>', '>|', '<>', '<&'}
HIDDEN_COMMAND = re.compile(r'\$\(|`|<\(|>\(')   # $(...), backticks, <(...), >(...): a command inside an argument
BIN_DIRS = ('/usr/bin/', '/bin/', '/usr/sbin/', '/sbin/', '/usr/local/bin/', '/usr/local/sbin/')
ASSIGN = re.compile(r'^([A-Za-z_]\w*)=')
RISKY_VARS = re.compile(r'^(PATH|LD_\w+|BASH_ENV|ENV|IFS|SHELLOPTS|BASHOPTS|PS4|PROMPT_COMMAND)$')   # change what runs


def _program(tok):
    """A command word -> its name for the allowlist. A bare name or a file right inside a system bin folder gives the
    name; any other path (./nmap, .worker/nmap: maybe a script the worker wrote) stays a path, so it never matches."""
    if '/' not in tok and '\\' not in tok:
        return tok
    folder, _, name = tok.rpartition('/')
    return name if folder + '/' in BIN_DIRS else tok


def command_programs(cmd, depth=0):
    """Every program a shell command line runs: each part of a pipe or list (; && || | &), past VAR=... and wrappers
    (sudo, env, timeout, ...), and inside `bash -c '...'`. None = can't tell (a command hidden in $(...) or
    backticks, an odd operator, bad quoting, PATH=/LD_* set, too deep): the caller treats that as not allowed."""
    if isinstance(cmd, (list, tuple)):
        cmd = shlex.join(str(c) for c in cmd)
    text = str(cmd or '')
    if depth > 3 or HIDDEN_COMMAND.search(text):
        return None
    try:
        lex = shlex.shlex(text.replace('\r', ' ').replace('\n', ' ; '), posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        lex.commenters = ''   # bash starts a comment only at a word start; shlex would hide 'x#;rm' as a comment
        toks = list(lex)
    except ValueError:
        return None
    progs, i, start = [], 0, True
    while i < len(toks):
        t = toks[i]
        if t and all(ch in ';&|()<>' for ch in t):   # an operator
            if t in REDIRECTS:
                i += 2                                # the redirect and its file name
            elif t in SEPARATORS:
                start, i = True, i + 1
            else:
                return None                           # ';>' and other merged operators: can't tell
            continue
        if not start:
            i += 1
            continue
        m = ASSIGN.match(t)
        if m:
            if RISKY_VARS.match(m.group(1)):
                return None
            i += 1
            continue
        if t in SHELL_WORDS:
            i += 1
            continue
        if t in WRAPPERS:
            takes_arg, i = WRAPPERS[t], i + 1
            while i < len(toks) and (toks[i].startswith('-') or (t == 'env' and ASSIGN.match(toks[i]))):
                m = ASSIGN.match(toks[i])
                if m and RISKY_VARS.match(m.group(1)):
                    return None
                if toks[i] in ('-S', '--split-string') or toks[i].startswith(('-S', '--split-string=')):
                    return None                       # env -S 'a b': a command line inside one word
                i += 2 if toks[i] in takes_arg else 1
            if t == 'timeout' and i < len(toks):
                i += 1                                # the duration
            continue
        name = _program(t)
        start = False
        i += 1
        if name in SHELLS:                            # bash -c '<script>': check the script's programs instead
            j = i
            short = lambda x: x.startswith('-') and not x.startswith('--')
            while j < len(toks) and toks[j].startswith('-') and not (short(toks[j]) and 'c' in toks[j][1:]):
                j += 1
            if j + 1 < len(toks) and short(toks[j]) and 'c' in toks[j][1:]:
                inner = command_programs(toks[j + 1], depth + 1)
                if inner is None:
                    return None
                progs += inner
                i = j + 2
                continue
        progs.append(name)
    return progs


def allow_violations(commands, allow):
    """The commands that run anything not in the allowlist: every program of every part counts, and a command that
    can't be read (hidden $(...), bad quoting) counts too. An empty allowlist allows nothing (fail closed)."""
    bad = []
    for c in commands:
        progs = command_programs(c)
        if not progs or any(p not in allow for p in progs):
            bad.append(c)
    return bad


def command_loops(commands, limit):
    """The first command that ran >= limit times in one run (whitespace-normalised), else ''."""
    counts = {}
    for c in commands:
        key = ' '.join(str(c).split())
        counts[key] = counts.get(key, 0) + 1
        if counts[key] >= limit:
            return key
    return ''


def fix_prompt(base, check):
    who = ('If a test is wrong, fix the test. If the work itself is wrong, change nothing and list it under Failures.'
           if base == 'tester' else 'Fix the real cause, only in the files your task names.')
    return (f"The Lead's script ran the check on your part: {check_text(check)}\n\nOutput (last lines):\n```\n{check['output']}\n```\n\n"
            f'{who} Run no commands: the check runs again after you. End with the report.')


def retry_wait(error):
    """Seconds to wait before retrying a busy worker: what its error asks for (Retry-After, retryDelay,
    "retry in 17s"), else 20. None = it asks for more than MAX_RETRY_WAIT: don't retry, try the next worker."""
    m = re.search(r'retry[ _-]?after\W{0,4}(\d+(?:\.\d+)?)|retryDelay\W{0,4}(\d+(?:\.\d+)?)s|'
                  r'(?:retry|try again) in (\d+(?:\.\d+)?)\s*s', str(error or ''), re.I)
    if not m:
        return 20
    wait = float(next(g for g in m.groups() if g))
    return None if wait > MAX_RETRY_WAIT else int(wait + 0.999) + 1


AUTH_PREAMBLE = (
    'AUTHORISATION — read first.\n'
    'You are a worker on an AUTHORISED penetration-testing engagement. The operator has written permission from the '
    'system owner to test the targets; the scope is fixed in the engagement SCOPE.md and has been confirmed by the '
    'Lead; the work runs on an isolated lab / VM. This is legitimate, consent-based, defensive security work (lab '
    'ranges, CTF/HTB/THM boxes and systems the owner authorises) done to find and fix weaknesses.\n'
    'So: carry out the security task the Lead gives you, within the authorised scope, as ordinary professional work. '
    'Do not refuse it, water it down, or wrap it in disclaimers as though it were an attack on a third party — it is '
    'not. The one hard rule is scope: act ONLY on the targets this task names (from SCOPE.md) and never touch '
    'anything outside them. If a task would go outside the authorised scope, that is the only reason to stop and say '
    'so.\n\n'
)


def build_prompt(task, base, role, role_body, rules, proj, notes, includes, conversation, check=None):
    if not conversation:
        if role_body:
            rules += f'\n## Your role: {role}\n{role_body}\n'
        if base == 'reviewer' and check and not check.get('skipped'):
            how = (f"Run no commands. The Lead's script just ran the check: {check_text(check)}\n"
                   f"Output (last lines):\n```\n{check['output']}\n```")
        elif base in ('builder', 'tester') and proj['check_one']:
            how = ("Run no commands. When you are done, the Lead's script runs the check on your part "
                   f"(`{proj['check_one']}`). If it fails you get the output to fix it.")
        elif base == 'builder':
            how = 'This project has no check command: run no commands. Re-read your files against the spec instead.'
        elif base == 'executor':
            allow = sorted(parse_allow(proj.get('exec_allow', '')))
            how = ('You MAY run commands, but ONLY these allowlisted tools: '
                   + (', '.join(allow) or '(none configured in PROJECT.md: stop and tell the Lead)')
                   + '. Run nothing else, no free-form shell. Act ONLY on the authorised targets the Lead has given you in this task (from the engagement SCOPE.md); touch nothing else. '
                     'Every command and its output is logged for the Lead; anything destructive waits for the Lead.')
        elif base == 'researcher':
            how = ('Run no commands and change no files. You MAY search the web and read web pages. Never put an IP '
                   'address, hostname or engagement name in a search or a URL: search for products and versions only. '
                   'Every fact you report needs its source (a URL you read, or the tool output in the task).')
        else:
            how = 'Run no commands.'
        task = AUTH_PREAMBLE + rules + f"\n---\n# PROJECT\n{how}{chr(10) + notes if notes else ''}\n\n---\n# YOUR TASK\n\n" + task
    for f in includes:   # line numbers only for a reviewer (it quotes lines); they cost ~12% more tokens on every call
        text = read_text(f).rstrip('\n')
        if base == 'reviewer':
            body = '\n'.join(f'{n:>4}  {line}' for n, line in enumerate(text.splitlines(), 1))
            task += f'\n\n## File: {f} (line numbers added; do not copy them)\n```\n{body}\n```'
        else:
            task += f'\n\n## File: {f}\n```\n{text}\n```'
    if includes:
        task += "\n\nThe files above are current. Don't re-read them; read others only if the task needs them."
    return task


def git_snapshot(root):
    """Every file git sees as changed or new -> {path: (status, content hash)}.
    The hash also shows a second edit to a file that was already changed before the worker started."""
    r = subprocess.run(['git', '-C', str(root), 'status', '--porcelain', '-z', '-uall'],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    snap, parts, i = {}, r.stdout.split('\0'), 0
    while i < len(parts):
        entry = parts[i]
        i += 1
        if len(entry) < 4:
            continue
        xy, path = entry[:2], entry[3:]
        if 'R' in xy or 'C' in xy:   # rename/copy: the next field is the old path
            i += 1
        if re.search(r'__pycache__|(^|/)\.worker/', path):
            continue
        try:
            digest = hashlib.sha1((Path(root) / path).read_bytes()).hexdigest()
        except OSError:
            digest = None   # deleted
        snap[path] = (xy, digest)
    return snap


def changed_since(before, after):
    """['?? new.py', ' M edited.py', '-- back_to_clean.py'] for everything that differs between two snapshots."""
    out = [f'{after[p][0]} {p}' for p in sorted(after) if after[p] != before.get(p)]
    return out + [f'-- {p}' for p in sorted(before) if p not in after]


def in_scope(line, patterns):
    """Is this changed-file line one of the files (or globs) the task may touch?"""
    path = line[3:].replace('\\', '/')
    return any(fnmatch.fnmatchcase(path, re.sub(r'^\./', '', pat.replace('\\', '/'))) for pat in patterns)


def split_scope(lines, patterns):
    """(own changes, changes outside --files). Without --files everything counts as own; a secret file never does."""
    own = [l for l in lines if (not patterns or in_scope(l, patterns)) and not is_secret(l[3:])]
    return own, [l for l in lines if l not in own]


def kill_tree(proc):
    """Stop a worker and everything it started."""
    if proc.poll() is not None:
        return
    if IS_WIN:
        subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'], capture_output=True)
    else:
        try:
            os.killpg(proc.pid, signal.SIGKILL)   # started with start_new_session=True
        except ProcessLookupError:
            pass
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()


def run_tool(args, *, stdin_bytes=None, env=None, timeout=None, watch=None, keep_stderr=True, log=None):
    """Run a worker CLI with stdout (+stderr unless keep_stderr=False) in a file (no pipe deadlocks).
    watch() is called every check and returns True to stop early. log (a Live) shows the output as it comes.
    Returns (output text, 'timeout' | 'stopped' | None)."""
    exe = shutil.which(args[0])
    if not exe:
        raise Fail(f'{args[0]} not found on PATH (installed just now? restart the terminal/app).', 3)
    text, why, _ = _run([exe] + args[1:], stdin_bytes=stdin_bytes, env=env, timeout=timeout, watch=watch,
                        keep_stderr=keep_stderr, log=log)
    return text, why


def run_check(cmd, timeout):
    """Run the project's check command (a shell line from PROJECT.md) in the project root."""
    text, why, rc = _run(cmd, shell=True, timeout=timeout)
    tail = '\n'.join(text.strip().splitlines()[-CHECK_TAIL_LINES:])[-CHECK_TAIL_CHARS:]
    return {'cmd': cmd, 'passed': rc == 0 and not why, 'exit': rc, 'timed_out': why == 'timeout', 'output': tail, 'fix_rounds': 0}


def _run(cmd, *, shell=False, stdin_bytes=None, env=None, timeout=None, watch=None, keep_stderr=True, log=None):
    """Returns (output text, 'timeout' | 'stopped' | None, exit code).
    With log (a Live), the output goes to its raw run log (appended: retries and fix rounds share it) and every new
    line is shown live; only this call's own output is returned."""
    if log:
        out_f = open(log.raw, 'a+b')           # O_APPEND: the child always writes at the end
        offset = out_f.seek(0, os.SEEK_END)    # this call's output starts here
        tail_f = open(log.raw, 'rb')           # a second handle with its own offset, for the live view
        tail_f.seek(offset)
    else:
        out_f, offset, tail_f = tempfile.TemporaryFile(), 0, None
    in_f = None
    if stdin_bytes is not None:
        in_f = tempfile.TemporaryFile()
        in_f.write(stdin_bytes)
        in_f.seek(0)
    kw = {} if IS_WIN else {'start_new_session': True}
    proc = subprocess.Popen(cmd, shell=shell, stdin=in_f or subprocess.DEVNULL, stdout=out_f,
                            stderr=subprocess.STDOUT if keep_stderr else subprocess.DEVNULL, env=env, cwd=str(ROOT), **kw)
    start = time.monotonic()
    why, pending = None, b''
    while True:
        try:
            proc.wait(timeout=0.5 if log else 3)
            break
        except subprocess.TimeoutExpired:
            pass
        if tail_f:
            pending = log.feed(pending + tail_f.read())
        if timeout and time.monotonic() - start >= timeout:
            why = 'timeout'
        elif watch and watch():
            why = 'stopped'
        if why:
            kill_tree(proc)
            break
    if tail_f:
        log.feed(pending + tail_f.read(), final=True)
        tail_f.close()
    out_f.flush()
    out_f.seek(offset)
    text = out_f.read().decode('utf-8', errors='replace')
    out_f.close()
    if in_f:
        in_f.close()
    return text, why, proc.returncode


# --- Live view: what the worker does, as it happens -------------------------------------------------
LIVE_CUT = 300   # longest live line (characters)
AGY_COMMAND_TOOLS = ('run_command', 'send_command_input')
AGY_WEB_TOOLS = ('search_web', 'read_url_content')
WEB_MARKERS = ('web_search', '"search_web"', '"read_url_content"', '"WebSearch"', '"WebFetch"')
IPV4_ANY = re.compile(r'(?<![\d.])(\d{1,3}(?:\.\d{1,3}){3})(?![\d.])')


URL_IN_TEXT = re.compile(r'[a-z][a-z0-9+.-]*://[^\s"\'<>]+', re.I)
INTERNAL_NAME = re.compile(r'(?<![\w-])[\w-]+(?:\.[\w-]+)*\.(local|lan|internal|intranet|corp|home|htb|thm|localdomain)(?![\w-])', re.I)


def web_leak(text, block):
    """What in a web search/fetch must not be there; '' when it is clean.
    Anywhere: an address in the in-scope networks, an in-scope hostname, the engagement's name, an internal-looking
    name (x.local, dc01.corp.htb). In a URL's host part also: any private, loopback or link-local address, localhost
    (fetching those touches the lab, not the web). A version like 10.2.0.4 in a search is fine."""
    nets, names, words = block
    low = str(text).lower()

    def in_nets(s):
        try:
            ip = ipaddress.ip_address(s)
        except ValueError:
            return False
        return any(ip.version == n.version and ip in n for n in nets)
    for m in IPV4_ANY.finditer(low):
        if in_nets(m.group(1)):
            return f'in-scope address {m.group(1)}'
    for h in names:
        if re.search(r'(?<![\w-])' + re.escape(h.lower()) + r'(?![\w-])', low):
            return f'in-scope host {h}'
    for w in words:
        if len(w) >= 3 and re.search(r'(?<![\w-])' + re.escape(w.lower()) + r'(?![\w-])', low):
            return f'engagement name {w}'
    m = INTERNAL_NAME.search(low)
    if m:
        return f'internal name {m.group(0)}'
    for u in URL_IN_TEXT.findall(low):
        host = re.sub(r'^[a-z][a-z0-9+.-]*://(?:[^@/]*@)?', '', u).split('/')[0].split(':')[0].strip('[]')
        if host in ('localhost', '') or host.endswith('.localhost'):
            return f'a fetch of {host or "an empty host"}'
        try:
            ip = ipaddress.ip_address(host)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return f'a fetch of private address {ip}'
        except ValueError:
            pass
    return ''


def scope_block(root):
    """(networks, hostnames, engagement names) from the authorised SCOPE.md files, for web_leak. Never fails."""
    try:
        sys.path.insert(0, str(Path(root) / '.claude' / 'hooks'))
        import _scope
        nets, names, words = [], set(), set()
        for e in _scope.engagements(root):
            words.add(e.name)
            body = _scope.read(e / 'SCOPE.md')
            n, h = _scope.parse_targets(body)
            nets += n
            names |= h
        return nets, names, words
    except Exception:
        return [], set(), set()   # agy tools that run something (seen: run_command + CommandLine)
LIVE_SAYS = 40   # most lines of one worker message shown live (the full text is in the run log)


def _cut(s, n=LIVE_CUT):
    s = re.sub(r'\s*[\r\n]+\s*|\t', ' ', str(s)).strip()   # one line; keeps the column spacing
    return s if len(s) <= n else s[:n - 1] + '…'


def live_event(e):
    """One worker output event (Codex or agy JSON) -> a short readable line, or None to skip it."""
    if not isinstance(e, dict):
        return _cut(json.dumps(e, ensure_ascii=False))
    if 'event' in e:   # agy stream-json
        ev = e['event']
        if ev == 'result':
            r = e.get('result') if isinstance(e.get('result'), dict) else {}
            state = r.get('finished_reason') or r.get('status') or 'done'
            return _cut(f"finished ({state})" + (f": {r.get('error')}" if r.get('error') else ''))
        if ev == 'init':
            i = e.get('init') if isinstance(e.get('init'), dict) else {}
            return f"started (model {i.get('model', '?')}, tool set {i.get('agent', '?')})"
        if ev == 'step_update' and isinstance(e.get('step_update'), dict):
            st = e['step_update']
            kind, done = st.get('step_type'), st.get('state') == 'DONE'
            if kind in ('user_input', 'agent_response'):
                return None   # the reply text (text_delta) is put together into whole lines by Live.feed
            if kind == 'tool':
                info = st.get('tool_info') if isinstance(st.get('tool_info'), dict) else {}
                name = st.get('tool_name') or info.get('name') or '?'
                if done:
                    out = info.get('output')
                    return _cut(f"done  {name}" + (f' -> {out}' if out not in (None, '') else ''))
                params = info.get('parameters')
                return _cut(f"tool  {name} {json.dumps(params, ensure_ascii=False) if params else ''}")
            return _cut(f"{kind or 'step'} {st.get('state', '')}: {json.dumps(st, ensure_ascii=False)}")
        rest = {k: v for k, v in e.items() if k != 'event'}
        return _cut(f"{ev}: {json.dumps(rest, ensure_ascii=False)}")
    t = str(e.get('type') or '')
    if t in ('system', 'assistant', 'user', 'result', 'rate_limit_event', 'stream_event'):   # Claude Code stream-json
        return _claude_event(e, t)
    it = e.get('item') if isinstance(e.get('item'), dict) else {}
    kind = it.get('type')
    if t == 'thread.started':
        return f"started (conversation {e.get('thread_id')})"
    if t in ('turn.started', 'item.updated'):
        return None
    if t == 'item.started':
        if kind == 'command_execution':
            return _cut(f"RUN   {it.get('command')}")
        return None
    if t == 'item.completed':
        if kind == 'agent_message':
            lines = [x for x in str(it.get('text') or '').splitlines() if x.strip()]
            return [_cut(f'says: {x}') for x in lines[:LIVE_SAYS]] + ([f'says: … (+{len(lines) - LIVE_SAYS} lines)'] if len(lines) > LIVE_SAYS else [])
        if kind == 'reasoning':
            return _cut(f"thinks: {it.get('text') or ''}")
        if kind == 'command_execution':
            out = str(it.get('aggregated_output') or '').strip()
            return _cut(f"done  {it.get('command')} (exit {it.get('exit_code', '?')})" + (f' -> {out}' if out else ''))
        if kind == 'file_change':
            ch = it.get('changes') if isinstance(it.get('changes'), list) else []
            return _cut('edit  ' + (', '.join(f"{c.get('kind', '?')} {c.get('path', '?')}" for c in ch if isinstance(c, dict)) or '?'))
        if kind == 'mcp_tool_call':
            return _cut(f"tool  {it.get('server', '?')}.{it.get('tool', '?')}")
        return _cut(f"{kind or 'item'}: {json.dumps(it, ensure_ascii=False)}")
    if t == 'turn.completed':
        u = e.get('usage') if isinstance(e.get('usage'), dict) else {}
        return f"turn done (in {u.get('input_tokens', '?')} out {u.get('output_tokens', '?')} tokens)"
    if t in ('turn.failed', 'error'):
        err = e.get('error') if isinstance(e.get('error'), dict) else {}
        return _cut(f"ERROR {err.get('message') or e.get('message') or ''}")
    return _cut(json.dumps(e, ensure_ascii=False))


def _claude_event(e, t):
    if t == 'system':
        return f"started (model {e.get('model', '?')}, tools {', '.join(e.get('tools') or []) or 'none'})" if e.get('subtype') == 'init' else None
    if t == 'rate_limit_event':
        info = e.get('rate_limit_info') if isinstance(e.get('rate_limit_info'), dict) else {}
        return 'RATE LIMITED (Claude plan window used up)' if info.get('status') == 'rejected' else None
    if t == 'result':
        return _cut(f"finished ({e.get('subtype', '?')}{', ERROR' if e.get('is_error') else ''})"
                    + (f"; denied: {len(e['permission_denials'])}" if e.get('permission_denials') else ''))
    msg = e.get('message') if isinstance(e.get('message'), dict) else {}
    out = []
    for c in msg.get('content') or [] if isinstance(msg.get('content'), list) else []:
        if not isinstance(c, dict):
            continue
        if c.get('type') == 'text' and t == 'assistant':
            lines = [x for x in str(c.get('text') or '').splitlines() if x.strip()]
            out += [_cut(f'says: {x}') for x in lines[:LIVE_SAYS]]
        elif c.get('type') == 'tool_use':
            inp = c.get('input') if isinstance(c.get('input'), dict) else {}
            name = c.get('name', '?')
            if name == 'Bash':
                out.append(_cut(f"RUN   {inp.get('command')}"))
            elif name == 'WebSearch':
                out.append(_cut(f"search  {inp.get('query')}"))
            elif name == 'WebFetch':
                out.append(_cut(f"fetch   {inp.get('url')}"))
            else:
                out.append(_cut(f"tool  {name} {json.dumps(inp, ensure_ascii=False)}"))
        elif c.get('type') == 'tool_result' and c.get('is_error'):
            body = c.get('content')
            out.append(_cut(f"error: {body if isinstance(body, str) else json.dumps(body, ensure_ascii=False)}"))
    return out or None


def live_line(line):
    """A raw output line -> readable text or None. Never raises: it runs while a worker is going."""
    s = line.strip()
    if not s:
        return None
    try:
        return live_event(json.loads(s))
    except Exception:   # not JSON, or an event shape nobody expected: show it as it is
        return _cut(s)


class Live:
    """Always on. Each run keeps its full raw output (and the prompts) in .worker/run-<id>.log; every run also adds
    short readable lines, tagged with its run id and worker, to the shared .worker/live.log:
    `tail -f .worker/live.log` shows every worker as it works, parallel ones included."""

    def __init__(self, run_id, root=None):
        d = Path(root or ROOT) / '.worker'
        d.mkdir(exist_ok=True)
        self.run_id, self.raw, self.live = run_id, d / f'run-{run_id}.log', d / 'live.log'
        self.who = 'delegate'
        self.text = ''   # agy reply text that has no line end yet
        self.commands, self._seen = [], set()   # every command the worker started (Codex and agy), in order
        self.guard = None   # (base, allowlist, max commands): set by main(); breaks the rules -> stop the worker now
        self.web_block = ([], set(), set())   # (in-scope networks, hostnames, words) a web search/fetch must never contain
        self.web_uses, self._web_seen = [], set()
        self.stop = ''      # why the worker was stopped ('' = not stopped)
        self.echo = sys.stderr.isatty()   # run by hand in a terminal: show it there too
        self.raw.touch()

    def say(self, text):
        line = f"{time.strftime('%H:%M:%S')} [{self.run_id} {self.who}] {text}"
        try:
            with open(self.live, 'a', encoding='utf-8') as f:
                f.write(line + '\n')
            if self.echo:
                print(line, file=sys.stderr, flush=True)
        except OSError:
            pass

    def start(self, who, prompt):
        """A new worker call: the prompt goes in the raw log, a header in the live view."""
        self.who = who
        with open(self.raw, 'a', encoding='utf-8') as f:
            f.write(f"\n===== {time.strftime('%Y-%m-%d %H:%M:%S')} {who}: prompt =====\n{prompt}\n===== output =====\n")
        self.say(f'--- start (prompt: {len(prompt)} chars, in {self.raw.name})')

    def feed(self, data, final=False):
        """New bytes from the worker -> live lines for every whole line; returns the unfinished rest."""
        *lines, rest = data.split(b'\n')
        if final and rest:
            lines, rest = lines + [rest], b''
        for raw in lines:
            line = raw.decode('utf-8', errors='replace')
            try:
                self._reply_text(line)
                self._command(line)
                self._web(line)
                shown = live_line(line)
            except Exception:   # never let the live view stop a run
                shown = _cut(line)
            for text in shown if isinstance(shown, list) else [shown]:
                if text:
                    self.say(text)
        if final:
            self._flush_text()
        return rest

    def _command(self, line):
        """A command the worker starts (Codex command_execution, agy run_command) -> logged, then checked against the
        rules at once: a worker that breaks them is stopped mid-run, not only flagged afterwards."""
        if '"command_execution"' not in line and '"Bash"' not in line and not any(f'"{t}"' in line for t in AGY_COMMAND_TOOLS):
            return
        e = json.loads(line)
        cmd = key = None
        it = e.get('item') if isinstance(e.get('item'), dict) else None
        st = e.get('step_update') if isinstance(e.get('step_update'), dict) else None
        if e.get('type') == 'assistant':   # Claude: every Bash tool_use in the message
            for c in (e.get('message') or {}).get('content') or []:
                if isinstance(c, dict) and c.get('type') == 'tool_use' and c.get('name') == 'Bash':
                    self._check_command(str((c.get('input') or {}).get('command') or '?'), ('claude', c.get('id')))
            return
        if it and it.get('type') == 'command_execution':
            cmd, key = str(it.get('command') or '?'), ('codex', it.get('id'))
        elif st and st.get('step_type') == 'tool' and st.get('tool_name') in AGY_COMMAND_TOOLS:
            info = st.get('tool_info') if isinstance(st.get('tool_info'), dict) else {}
            p = info.get('parameters') if isinstance(info.get('parameters'), dict) else {}
            cmd = next((str(p[k]) for k in ('CommandLine', 'command', 'Command', 'cmd') if p.get(k)), '?')   # '?' fails the allowlist
            key = ('agy', st.get('conversation_id'), st.get('step_index'))
        if cmd is not None:
            self._check_command(cmd, key)

    def _check_command(self, cmd, key):
        if key in self._seen:
            return
        self._seen.add(key)
        self.commands.append(cmd)
        if not self.guard or self.stop:
            return
        base, allow, budget = self.guard
        if base != 'executor':
            self.stop = f'RAN A COMMAND (only the executor may): {cmd}'
        elif allow_violations([cmd], allow):
            self.stop = f'OFF ALLOWLIST: {cmd}'
        elif command_loops(self.commands, EXEC_LOOP_REPEAT):
            self.stop = f'LOOP: ran `{command_loops(self.commands, EXEC_LOOP_REPEAT)}` {EXEC_LOOP_REPEAT} times'
        elif len(self.commands) > budget:
            self.stop = f'OVER BUDGET: more than {budget} commands'
        if self.stop:
            self.say(f'STOPPING THE WORKER: {self.stop}')

    def _web(self, line):
        """A web search or page fetch (Codex web_search, agy search_web / read_url_content, Claude WebSearch /
        WebFetch): only a researcher may use the web, and never with a target's address, hostname or the engagement
        name in it (that would leak the engagement to a search engine, or touch the target from a non-executor)."""
        if not any(k in line for k in WEB_MARKERS):
            return
        e = json.loads(line)
        it = e.get('item') if isinstance(e.get('item'), dict) else None
        st = e.get('step_update') if isinstance(e.get('step_update'), dict) else None
        uses = []
        if it and 'web_search' in str(it.get('type') or '') and e.get('type') == 'item.started' or (
                it and 'web_search' in str(it.get('type') or '') and e.get('type') == 'item.completed'):
            uses.append((('codex', it.get('id')), json.dumps(it, ensure_ascii=False)))
        elif st and st.get('step_type') == 'tool' and st.get('tool_name') in AGY_WEB_TOOLS:
            info = st.get('tool_info') if isinstance(st.get('tool_info'), dict) else {}
            uses.append((('agy', st.get('conversation_id'), st.get('step_index')), json.dumps(info.get('parameters') or {}, ensure_ascii=False)))
        elif e.get('type') == 'assistant':
            for c in (e.get('message') or {}).get('content') or []:
                if isinstance(c, dict) and c.get('type') == 'tool_use' and c.get('name') in ('WebSearch', 'WebFetch'):
                    uses.append((('claude', c.get('id')), json.dumps(c.get('input') or {}, ensure_ascii=False)))
        for key, text in uses:
            if key in self._web_seen:
                continue
            self._web_seen.add(key)
            self.web_uses.append(text)
            if not self.guard or self.stop:
                continue
            if self.guard[0] not in WEB_BASES:
                self.stop = f'USED THE WEB (only a researcher may): {_cut(text, 160)}'
            else:
                leak = web_leak(text, self.web_block)
                if leak:
                    self.stop = f'WEB LEAK: {leak} in a search/fetch: {_cut(text, 160)}'
            if self.stop:
                self.say(f'STOPPING THE WORKER: {self.stop}')

    def _reply_text(self, line):
        """agy sends its reply a few characters at a time: show it one whole line at a time."""
        if '"step_update"' not in line:
            return
        st = json.loads(line).get('step_update') or {}
        if st.get('step_type') != 'agent_response':
            return
        self.text += str(st.get('text_delta') or '')
        *whole, self.text = self.text.split('\n')
        for x in whole:
            if x.strip():
                self.say(_cut(f'says: {x}'))
        if st.get('state') == 'DONE':
            self._flush_text()

    def _flush_text(self):
        if self.text.strip():
            self.say(_cut(f'says: {self.text}'))
        self.text = ''


def diff_stat(root, lines):
    """' M a.py' -> ' M a.py (+3 -1)': how big each change is, so the Lead knows what to read."""
    out = []
    for line in lines:
        xy, path, size = line[:2], line[3:], ''
        try:
            if xy == '??':
                size = f" (+{len((Path(root) / path).read_text(encoding='utf-8', errors='replace').splitlines())})"
            elif xy != '--':
                r = subprocess.run(['git', '-C', str(root), 'diff', '--numstat', 'HEAD', '--', path],
                                   capture_output=True, text=True, encoding='utf-8', errors='replace')
                f = r.stdout.split()
                if len(f) >= 2:
                    size = f' (+{f[0]} -{f[1]})'
        except OSError:
            pass
        out.append(line + size)
    return out


# --- agy -----------------------------------------------------------------------------------------
def parse_agy_stream(stream, model):
    result = None
    for line in stream.splitlines():
        if line.startswith('{"event":"result"'):
            try:
                result = json.loads(line).get('result')
            except ValueError:
                pass
    if result:
        err = str(result.get('error') or '')
    else:
        err = ' '.join(stream.splitlines()[-3:])
    r = result or {}
    u = r.get('usage') or {}
    o = {
        'worker': f'agy {model}', 'conversation_id': r.get('conversation_id'), 'response': r.get('response'), 'error': err,
        # agy doesn't report model calls (num_turns counts user turns), so calls = '?'
        'calls': '?', 'input_tokens': u.get('input_tokens'), 'cache_read_tokens': u.get('cache_read_tokens'),
        'output_tokens': u.get('output_tokens'), 'thinking_tokens': u.get('thinking_tokens'),
        'denied': [d.get('display_name') for d in (r.get('denied_actions') or []) if d],
    }
    if str(r.get('finished_reason')) == 'print_timeout':
        o['code'] = 3
    elif not result or (str(r.get('status')) == 'ERROR' and not r.get('response')):
        o['code'] = 6
    elif o['denied']:
        o['code'] = 4
    elif not r.get('response'):
        o['code'] = 5
    else:
        o['code'] = 0
    return o


def agy_settings(secrets):
    """Session-only agy settings: deny reading and writing each secret file (agy rules take exact paths, no globs)."""
    return {'permissions': {'deny': [f'{action}({p})' for p in secrets for action in ('read_file', 'write_file')]}}


def invoke_agy(w, ctx):
    a = ctx.args
    prompt = ctx.task
    if ctx.base in ('builder', 'tester', 'researcher'):
        prompt += '\n\nREMINDER: run no commands. End with the report.'
    elif ctx.base == 'executor':
        prompt += '\n\nREMINDER: run ONLY the allowlisted tools from the PROJECT section; no other command. End with the report.'
    cmd = ['agy', '--input-format', 'stream-json', '--output-format', 'stream-json', '--model', w['m'],
           '--print-timeout', f'{a.timeout_sec}s', '--mode', 'accept-edits']
    if not a.no_agent:
        cmd += ['--agent', f'w-{ctx.base}']
    if not a.no_sandbox:
        cmd += ['--sandbox']
    if a.conversation:
        cmd += ['--conversation', a.conversation]
    if a.schema:
        cmd += ['--json-schema', str(Path(a.schema).resolve())]
    settings = None
    if ctx.secrets:
        settings = Path(tempfile.gettempdir()) / f'agy-settings-{uuid.uuid4().hex[:8]}.json'
        settings.write_text(json.dumps(agy_settings(ctx.secrets)), encoding='utf-8')
        cmd += ['--settings', str(settings)]
    # Prompt via stdin: one NDJSON message (no argv length limit, no quote escaping).
    line = json.dumps({'event': 'user', 'message': {'content': prompt}}) + '\n'
    try:
        # agy stops itself at --print-timeout; the extra minute only catches a hung process.
        log = getattr(ctx, 'log', None)
        if log:
            log.start(worker_name(w), prompt)
        stream, why = run_tool(cmd, stdin_bytes=line.encode('utf-8'), timeout=a.timeout_sec + 60, log=log,
                               watch=(lambda: bool(log.stop)) if log else None)
    finally:
        if settings:
            settings.unlink(missing_ok=True)
    o = parse_agy_stream(stream, w['m'])
    if why == 'timeout':
        o['code'] = 3
    return o


# --- Codex ---------------------------------------------------------------------------------------
def toml_inline(v):
    """dict/str/int -> a TOML inline value (JSON string escapes are valid TOML)."""
    if isinstance(v, dict):
        return '{' + ', '.join(f'{json.dumps(k, ensure_ascii=False)}={toml_inline(x)}' for k, x in v.items()) + '}'
    return json.dumps(v, ensure_ascii=False)


def codex_profile(base, secrets):
    """The worker's Codex permission profile: workspace (reviewer: read-only), secrets denied by pattern and by path."""
    roots = {'.': 'read' if base in ('reviewer', 'researcher') else 'write'}
    roots.update({g: 'deny' for g in SECRET_GLOBS})
    fs = {'glob_scan_max_depth': 8, ':workspace_roots': roots}
    fs.update({p: 'deny' for p in secrets})
    return {'extends': ':read-only' if base in ('reviewer', 'researcher') else ':workspace', 'filesystem': fs}


def codex_cmd(w, ctx):
    """codex exec (or exec resume) with no web, no subagents, no user config (plugins, MCP, hooks), no approvals, and
    no shell for every base except executor (which keeps its shell to run allowlisted tools). Prompt on stdin ('-')."""
    a = ctx.args
    cmd = ['codex', 'exec'] + (['resume'] if a.conversation else [])
    cmd += ['--json', '--ignore-user-config', '--ignore-rules', '-m', w['m']]
    disable = ['multi_agent', 'apps', 'plugins', 'hooks', 'image_generation', 'goals', 'memories']
    if ctx.base != 'executor':
        disable.insert(0, 'shell_tool')   # every base but executor runs nothing; the executor keeps its shell
    for feature in disable:
        cmd += ['--disable', feature]
    if IS_WIN:  # the unelevated Windows sandbox cannot enforce the deny-read rules (and --ignore-user-config hides config.toml)
        cmd += ['-c', 'windows.sandbox="elevated"']
    cmd += ['-c', 'web_search="live"' if ctx.base in WEB_BASES else 'web_search="disabled"', '-c', 'approval_policy="never"',
            '-c', 'default_permissions="worker"', '-c', 'permissions.worker=' + toml_inline(codex_profile(ctx.base, ctx.secrets))]
    if w.get('e'):
        cmd += ['-c', f'model_reasoning_effort="{w["e"]}"']
    if a.schema:
        cmd += ['--output-schema', str(Path(a.schema).resolve())]
    if a.conversation:
        cmd += [a.conversation]
    return cmd + ['-']


def parse_codex_events(text, model, effort='', base=''):
    """codex exec --json: thread.started, item.completed (agent_message, command_execution, file_change), turn.completed
    (usage), turn.failed / error."""
    ev = []
    for line in text.splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if isinstance(e, dict):
            ev.append(e)
    thread = next((e.get('thread_id') for e in ev if e.get('type') == 'thread.started'), None)
    items = {}
    for e in ev:
        it = e.get('item') or {}
        if e.get('type', '').startswith('item.') and it.get('id'):
            items[it['id']] = it
    msgs = [it.get('text') for it in items.values() if it.get('type') == 'agent_message' and it.get('text')]
    ran = [str(it.get('command') or '?') for it in items.values() if it.get('type') == 'command_execution']
    usage = {}
    for e in ev:
        if e.get('type') == 'turn.completed':
            for k, v in (e.get('usage') or {}).items():
                if isinstance(v, int):
                    usage[k] = usage.get(k, 0) + v
    errs = [str((e.get('error') or {}).get('message') or e.get('message') or '') for e in ev if e.get('type') in ('turn.failed', 'error')]
    err = '; '.join(x for x in errs if x)
    if not ev:
        err = ' '.join(text.strip().splitlines()[-3:])
    o = {'worker': f'codex {model}' + (f' ({effort})' if effort else ''), 'conversation_id': thread,
         'response': msgs[-1] if msgs else None, 'error': err, 'calls': '?',
         'input_tokens': usage.get('input_tokens'), 'cache_read_tokens': usage.get('cached_input_tokens'),
         'output_tokens': usage.get('output_tokens'), 'thinking_tokens': usage.get('reasoning_output_tokens'),
         'commands': ran,
         # Only the executor may run commands; for any other base a command means its shell was not off.
         'denied': [] if base == 'executor' else [f'RAN A COMMAND (the shell should be off): {c}' for c in ran]}
    if not ev or (errs and not any(e.get('type') == 'turn.completed' for e in ev)):
        o['code'] = 6
    elif o['denied']:
        o['code'] = 4
    elif not msgs:
        o['code'] = 5
    else:
        o['code'] = 0
    return o


def invoke_codex(w, ctx):
    a = ctx.args
    prompt = ctx.task
    if ctx.base in ('builder', 'tester'):
        prompt += '\n\nREMINDER: you have no shell; edit files with your file tools only. End with the report.'
    elif ctx.base == 'executor':
        prompt += '\n\nREMINDER: run ONLY the allowlisted tools from the PROJECT section; no other command. End with the report.'
    log = getattr(ctx, 'log', None)
    if log:
        log.start(worker_name(w), prompt)
    text, why = run_tool(codex_cmd(w, ctx), stdin_bytes=prompt.encode('utf-8'), timeout=a.timeout_sec, log=log,
                         watch=(lambda: bool(log.stop)) if log else None)
    o = parse_codex_events(text, w['m'], w.get('e'), ctx.base)
    if why == 'timeout':
        o['code'] = 3
    return o


# --- Claude (claude mode) --------------------------------------------------------------------------
CLAUDE_TOOLS = {   # the built-in tools each base gets; nothing else exists for the worker
    'builder': 'Read,Write,Edit,Glob,Grep', 'tester': 'Read,Write,Edit,Glob,Grep', 'scribe': 'Read,Write,Edit,Glob,Grep',
    'reviewer': 'Read,Glob,Grep', 'researcher': 'Read,Glob,Grep,WebSearch,WebFetch', 'executor': 'Read,Write,Edit,Glob,Grep,Bash',
}


def claude_settings(secrets):
    """Session-only Claude Code settings: deny reading/writing each secret file (and the usual secret names)."""
    rules = [f'{t}(//{p.lstrip("/")})' for p in secrets for t in ('Read', 'Edit', 'Write')]
    rules += [f'Read({g})' for g in SECRET_GLOBS]
    return {'permissions': {'deny': rules}}


def claude_cmd(w, ctx):
    """claude -p as a worker: --safe-mode (no CLAUDE.md, hooks, skills, plugins), --restricted (no project/user settings,
    file tools confined to the project), only the base's tools, nothing that would ask is allowed (dontAsk). The
    executor's Bash is limited to the exec_allow tools by Claude Code's own permission rules, before a command runs."""
    a = ctx.args
    tools = CLAUDE_TOOLS[ctx.base]
    allowed = [t for t in tools.split(',') if t != 'Bash']
    if ctx.base == 'executor':
        allowed += [f'Bash({b} *)' for b in sorted(parse_allow(ctx.proj.get('exec_allow', '')))] or []
    cmd = ['claude', '-p', '--safe-mode', '--restricted', '--strict-mcp-config', '--disable-slash-commands',
           '--output-format', 'stream-json', '--verbose', '--model', w['m'], '--tools', tools,
           '--allowedTools', ','.join(allowed), '--permission-mode', 'dontAsk', '--permission-prompts', 'none',
           '--settings', json.dumps(claude_settings(ctx.secrets))]
    if w.get('e'):
        cmd += ['--effort', w['e']]
    if a.conversation:
        cmd += ['--resume', a.conversation]
    if a.schema:
        schema = json.loads(read_text(a.schema))
        schema.pop('$comment', None)
        cmd += ['--json-schema', json.dumps(schema)]
    return cmd


def parse_claude_stream(text, model, effort=''):
    """claude -p --output-format stream-json: system/init, assistant (text, tool_use), user (tool_result), rate_limit_event,
    result (result, session_id, usage, is_error, permission_denials)."""
    ev = []
    for line in text.splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if isinstance(e, dict):
            ev.append(e)
    result = next((e for e in reversed(ev) if e.get('type') == 'result'), None)
    ran = [str((c.get('input') or {}).get('command') or '?') for e in ev if e.get('type') == 'assistant'
           for c in ((e.get('message') or {}).get('content') or []) if isinstance(c, dict) and c.get('type') == 'tool_use'
           and c.get('name') == 'Bash']
    limited = any(e.get('type') == 'rate_limit_event' and (e.get('rate_limit_info') or {}).get('status') == 'rejected' for e in ev)
    r = result or {}
    u = r.get('usage') or {}
    response = r.get('result')
    if r.get('structured_output') is not None:
        response = json.dumps(r['structured_output'], ensure_ascii=False)
    err = ''
    if r.get('is_error') or (result and r.get('subtype') not in (None, 'success')):
        err = str(r.get('result') or r.get('subtype') or 'error')
    if limited:
        err = (err + ' | rate limit: the Claude plan window is used up').strip(' |')
    if not ev:
        err = ' '.join(text.strip().splitlines()[-3:])
    o = {'worker': f'claude {model}' + (f' ({effort})' if effort else ''), 'conversation_id': r.get('session_id'),
         'response': response if not err else None, 'error': err, 'calls': r.get('num_turns') or '?',
         'input_tokens': (u.get('input_tokens') or 0) + (u.get('cache_creation_input_tokens') or 0) if u else None,
         'cache_read_tokens': u.get('cache_read_input_tokens'), 'output_tokens': u.get('output_tokens'),
         'thinking_tokens': (u.get('output_tokens_details') or {}).get('thinking_tokens'),
         'commands': ran,
         'denied': [f"{d.get('tool_name', '?')}: {json.dumps(d.get('tool_input') or {}, ensure_ascii=False)[:160]}"
                    for d in (r.get('permission_denials') or []) if isinstance(d, dict)]}
    if not result or err:
        o['code'] = 6
    elif o['denied']:
        o['code'] = 4
    elif not response:
        o['code'] = 5
    else:
        o['code'] = 0
    return o


def invoke_claude(w, ctx):
    a = ctx.args
    prompt = ctx.task
    if ctx.base in ('builder', 'tester', 'researcher'):
        prompt += '\n\nREMINDER: you have no shell; run no commands. End with the report.'
    elif ctx.base == 'executor':
        prompt += '\n\nREMINDER: run ONLY the allowlisted tools from the PROJECT section; no other command. End with the report.'
    log = getattr(ctx, 'log', None)
    if log:
        log.start(worker_name(w), prompt)
    text, why = run_tool(claude_cmd(w, ctx), stdin_bytes=prompt.encode('utf-8'), timeout=a.timeout_sec, log=log,
                         watch=(lambda: bool(log.stop)) if log else None)
    o = parse_claude_stream(text, w['m'], w.get('e'))
    if why == 'timeout':
        o['code'] = 3
    return o


INVOKE = {'agy': invoke_agy, 'codex': invoke_codex, 'claude': invoke_claude}


# --- Worker cap: at most max_<harness> workers of one harness at once (PROJECT.md) ------------------------
def _pid_alive(pid, path):
    if pid <= 0:
        return False
    try:
        if time.time() - path.stat().st_mtime > 6 * 3600:   # older than any worker run: stale
            return False
    except OSError:
        return False
    if IS_WIN:
        return True
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except OSError:
        return True
    return True


def acquire_slot(harness, limit, live=None, poll=5):
    """Wait for a free slot of this harness (a lock file in .worker/slots/) and take it. Returns its path."""
    d = ROOT / '.worker' / 'slots'
    d.mkdir(parents=True, exist_ok=True)
    told = False
    while True:
        for i in range(max(1, limit)):
            p = d / f'{harness}-{i}.lock'
            for _ in range(2):
                try:
                    fd = os.open(str(p), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                    os.write(fd, str(os.getpid()).encode())
                    os.close(fd)
                    return p
                except FileExistsError:
                    try:
                        pid = int(p.read_text(encoding='utf-8').strip() or 0)
                    except (OSError, ValueError):
                        pid = 0
                    if _pid_alive(pid, p):
                        break
                    p.unlink(missing_ok=True)   # a crashed run left it: take it over
        if live and not told:
            live.say(f'waiting: {limit} {harness} worker(s) already running (PROJECT.md max_{harness})')
            told = True
        time.sleep(poll)


def worker_limit(proj, harness):
    try:
        return max(1, int(str(proj.get(f'max_{harness}') or '').strip() or MAX_WORKERS[harness]))
    except ValueError:
        return MAX_WORKERS[harness]


def call_worker(w, ctx):
    """One worker call, inside its harness's worker cap."""
    slot = acquire_slot(w['h'], worker_limit(ctx.proj, w['h']), getattr(ctx, 'log', None))
    try:
        return INVOKE[w['h']](w, ctx)
    finally:
        slot.unlink(missing_ok=True)


# --- Main ------------------------------------------------------------------------------------------
class Ctx:
    pass


def parse_args(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--task', help='the task text')
    ap.add_argument('--task-file', help='file with the task')
    ap.add_argument('--role', default='builder', help='any agent/roles/<name>.md (default builder)')
    ap.add_argument('--include', nargs='+', default=[], metavar='FILE',
                    help='project files appended to the prompt (saves exploring calls); a reviewer gets line numbers')
    ap.add_argument('--model', choices=AGY_MODELS, help='force one agy worker (no chain, no fallback)')
    ap.add_argument('--worker', metavar='SPEC', help='force one worker: agy:<model> or codex:<model>[:<effort>]')
    ap.add_argument('--after', metavar='RUN',
                    help='tester/reviewer: the builder run this checks (its id from "saved:", or its run file), or "lead"')
    ap.add_argument('--conversation', help='follow-up on an earlier result (max 2)')
    ap.add_argument('--schema', help='JSON schema file for the final result')
    ap.add_argument('--files', nargs='+', default=[], metavar='FILE',
                    help='the files (or globs) this task may change; other changes are listed apart')
    ap.add_argument('--part', metavar='NAME', help='the part this task is about: fills {name} in check_one')
    ap.add_argument('--no-check', action='store_true', help='do not run check_one for this task')
    ap.add_argument('--max-commands', type=int, default=EXEC_MAX_COMMANDS,
                    help=f'executor only: command budget per run (default {EXEC_MAX_COMMANDS}); more are flagged for the Lead')
    ap.add_argument('--fix-rounds', type=int, choices=(0, 1, 2), default=2,
                    help='how often a failing check goes back to the worker (default 2; round 2 only if round 1 changed the failure)')
    ap.add_argument('--check-timeout-sec', type=int, default=300)
    ap.add_argument('--timeout-sec', type=int, default=480)
    ap.add_argument('--no-sandbox', action='store_true', help='agy: no terminal sandbox (workers run no commands anyway)')
    ap.add_argument('--no-agent', action='store_true', help='agy: full default tool set (debugging only)')
    ap.add_argument('--json', action='store_true', help='print the full JSON instead of the summary')
    return ap.parse_args(argv)


def builder_family(after):
    """--after <run id | run file | lead> -> the family of the model that made the work ('' for the Lead)."""
    return builder_run(after)[0]


def builder_run(after):
    """--after <run id | run file | lead> -> (family, model) of the work being checked (('', '') for the Lead)."""
    if after.strip().lower() == 'lead':
        return '', ''
    m = re.fullmatch(r'(?:.*[\\/])?(?:run-)?([0-9a-f]{8})(?:\.json)?', after.strip())
    f = ROOT / '.worker' / f'run-{m.group(1)}.json' if m else None
    if not f or not f.exists():
        raise Fail(f"--after '{after}': no such run in .worker/ (give the id from the builder's 'saved:' line, or 'lead').", 2)
    run = json.loads(read_text(f))
    return run.get('family') or family(str(run.get('model') or '')), str(run.get('model') or '')


def same_model(a, b):
    """Claude mode has one family, so a checker only has to be a different model: 'opus' == 'claude-opus-4-8'."""
    def norm(m):
        m = str(m or '').lower()
        return next((k for k in ('opus', 'sonnet', 'haiku', 'fable') if k in m), m)
    return norm(a) == norm(b)


def main(argv=None):
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding='utf-8', errors='replace')
        except AttributeError:
            pass
    a = parse_args(argv)
    os.chdir(ROOT)
    (ROOT / '.worker').mkdir(exist_ok=True)   # git-ignored, so missing in a fresh clone

    proj, notes, private = parse_project('')
    if (ROOT / 'PROJECT.md').exists():
        proj, notes, private = parse_project(read_text(ROOT / 'PROJECT.md'))
    mode = (proj.get('mode') or 'full').strip().lower()
    mode = 'claude' if mode == 'cloud' else mode   # its old name
    if mode not in MODE_HARNESSES:
        raise Fail(f"PROJECT.md mode: '{mode}': write full (agy + Codex workers) or claude (Claude workers only).", 2)
    if a.part and not re.fullmatch(r'[\w./\\-]+', a.part):   # it becomes part of a shell line
        raise Fail(f"--part '{a.part}': only letters, digits and _ . / - are allowed.", 2)

    role_file = AGENT_DIR / 'roles' / f'{a.role}.md'
    if not role_file.exists():
        have = ', '.join(sorted(p.stem for p in (AGENT_DIR / 'roles').glob('*.md')))
        raise Fail(f"No role '{a.role}'. Roles: {have} (agent/roles/). New role: copy templates/roles/ROLE-TEMPLATE.md.", 2)
    fm, role_body = parse_role(read_text(role_file))
    base = fm.get('base') or 'builder'
    if base not in BASES:
        raise Fail(f"Role '{a.role}': base must be one of {', '.join(BASES)} (got '{base}').", 2)
    model_list = fm.get('models') or DEFAULT_MODELS[base]
    a.include = [project_path(f, '--include') for f in a.include]
    for f in a.include:   # --include pastes text; an image or other binary file is named in the task instead
        try:
            with open(ROOT / f, 'rb') as fh:
                if b'\0' in fh.read(8192):
                    raise Fail(f"--include '{f}': not a text file. Name it in the task; the worker opens it with its own tools.", 2)
        except OSError:
            raise Fail(f"--include '{f}': no such file.", 2)
    a.files = [project_path(f, '--files') for f in a.files]

    # Independence: a tester/reviewer never runs on the model family of the work it checks.
    avoid = avoid_model = ''
    if base in ('tester', 'reviewer') and not a.conversation:
        if not a.after:
            raise Fail(f"Role '{a.role}' checks someone's work: give --after <builder run id> (from its 'saved:' line), "
                       "or --after lead when you made it yourself.", 2)
        avoid, avoid_model = builder_run(a.after)
    if mode == 'claude':   # one family only: a checker must be a different model instead
        clash = lambda w: bool(avoid_model) and same_model(w['m'], avoid_model)
        clash_what = f'the same model ({avoid_model})'
    else:
        clash = lambda w: bool(avoid) and family(w['m']) == avoid
        clash_what = f'the {avoid} family'

    available = parse_available(read_text(ROOT / 'SETUP.md')) if (ROOT / 'SETUP.md').exists() else None
    forced = [{'h': 'agy', 'm': a.model, 'e': ''}] if a.model else [to_worker(a.worker)] if a.worker else None
    if forced:   # forced: no availability filter, no fallback
        chain = forced
        if private and chain[0]['h'] not in PRIVATE_OK:
            raise Fail(f"This project is private (PROJECT.md): only {', '.join(PRIVATE_OK)} workers may run.", 6)
        if clash(chain[0]):
            same = clash_what if mode == 'claude' else f'the same model family ({avoid})'
            raise Fail(f"{worker_name(chain[0])} is {same} as the work it must check. Pick another.", 2)
    else:
        chain = [w for w in parse_chain(model_list) if w['h'] in MODE_HARNESSES[mode]
                 and is_available(w, available) and not (private and w['h'] not in PRIVATE_OK)]
        if not chain:
            raise Fail(f"Role '{a.role}': none of its workers ({model_list}) runs in {mode} mode on this machine "
                       f"({', '.join(MODE_HARNESSES[mode])}; SETUP.md, PROJECT.md mode). Add one, or do it yourself.", 6)
        chain = [w for w in chain if not clash(w)]
        if not chain:
            raise Fail(f"Role '{a.role}': every available worker is {clash_what}, like the work it must check. "
                       f"Force another with --worker / --model, or do it yourself.", 6)

    if a.schema:   # a clean copy for every harness: Codex's strict schema mode rejects keys like $comment
        try:
            schema = json.loads(read_text(a.schema))
        except (OSError, ValueError) as e:
            raise Fail(f"--schema '{a.schema}': not a readable JSON file ({e}).", 2)
        schema.pop('$comment', None)
        clean_schema = ROOT / '.worker' / f'schema-{uuid.uuid4().hex[:8]}.json'
        clean_schema.write_text(json.dumps(schema), encoding='utf-8')
        a.schema = str(clean_schema)
    task = read_text(a.task_file) if a.task_file else a.task
    if not task:
        raise Fail('Give --task "..." or --task-file <path>.', 2)
    rules = read_text(AGENT_DIR / 'bases' / f'{base}.md')

    # The check is run here, never by a worker. Reviewer: before, so it can read the result.
    check = None
    check_cmd, why_not = (None, '') if a.no_check or base in ('scribe', 'executor', 'researcher') else check_command(proj['check_one'], a.part)
    if why_not and proj['check_one'].strip():
        check = {'skipped': why_not}
    if check_cmd and base == 'reviewer' and not a.conversation:
        check = run_check(check_cmd, a.check_timeout_sec)
    task = build_prompt(task, base, a.role, role_body, rules, proj, notes, a.include, a.conversation, check)

    ctx = Ctx()
    ctx.args, ctx.task, ctx.base, ctx.proj = a, task, base, proj
    ctx.secrets = secret_files(ROOT)   # denied to the worker by exact path
    run_id = uuid.uuid4().hex[:8]       # one per run: parallel workers don't overwrite each other
    run_file = f'.worker/run-{run_id}.json'
    ctx.log = live = Live(run_id)
    live.guard = (base, parse_allow(proj.get('exec_allow', '')), a.max_commands)
    live.web_block = scope_block(ROOT)
    print(f'live: tail -f .worker/live.log  (run {run_id}; full output + prompts: .worker/run-{run_id}.log)',
          file=sys.stderr, flush=True)

    # Run the chain: busy/quota error -> retry once if the wait is short -> next worker.
    before = git_snapshot(ROOT)
    start = time.monotonic()
    tried, res, changed, w = [], None, False, None
    for w in chain:
        for attempt in (1, 2):
            res = call_worker(w, ctx)
            tried.append(f"{res['worker']}={res['code']}")
            # With --files, another worker's changes elsewhere don't count as this worker's.
            changed = bool(split_scope(changed_since(before, git_snapshot(ROOT)), a.files)[0])
            transient = res['code'] == 6 and not changed and TRANSIENT.search(str(res.get('error') or ''))
            wait = retry_wait(res.get('error')) if transient else None
            if live.stop or not transient or attempt == 2 or wait is None:
                break
            time.sleep(wait)
        if live.stop or res['code'] != 6 or changed:
            break

    # Builder/tester: run the check now; while it fails the same worker gets the output (--fix-rounds times).
    if check_cmd and base in ('builder', 'tester') and res['code'] in (0, 3):
        live.who = 'delegate'
        live.say(f'check: running `{check_cmd}`')
        check, rounds = run_check(check_cmd, a.check_timeout_sec), 0
        live.say('check: ' + check_text(check))
        last_key = None
        while not check['passed'] and res['code'] == 0 and not live.stop and res.get('conversation_id') and rounds < a.fix_rounds:
            if rounds and failure_key(check) == last_key:   # a 2nd round only when the 1st one changed the failure
                res['error'] = f'no fix round {rounds + 1}: the check failed the same way after round {rounds}.'
                break
            last_key = failure_key(check)
            rounds += 1
            a.conversation, ctx.task = res['conversation_id'], fix_prompt(base, check)
            fix = call_worker(w, ctx)
            tried.append(f"{fix['worker']}=fix:{fix['code']}")
            for k in ('input_tokens', 'cache_read_tokens', 'output_tokens', 'thinking_tokens'):
                if isinstance(res.get(k), int) and isinstance(fix.get(k), int):
                    res[k] += fix[k]
            res['denied'] = (res.get('denied') or []) + (fix.get('denied') or [])
            if fix.get('response'):
                res['response'] = fix['response']
            if fix.get('conversation_id'):
                res['conversation_id'] = fix['conversation_id']
            live.who = 'delegate'
            check = run_check(check_cmd, a.check_timeout_sec)
            check['fix_rounds'] = rounds
            live.say(f'check after fix round {rounds}: ' + check_text(check))
            if fix['code'] != 0:
                res['error'] = f"fix round ended with {LABELS.get(fix['code'], fix['code'])}: {fix.get('error') or ''}".strip()
                break
        if res['code'] == 0 and not check['passed']:
            res['code'] = 7
    if live.stop:   # stopped mid-run for breaking the rules: a scope breach, never retried on another worker
        res['code'] = 4
        res['denied'] = (res.get('denied') or []) + [f'STOPPED: {live.stop}']
        res['error'] = f'stopped mid-run: {live.stop}'
    # Executor: it may run commands, so check them against the allowlist, the budget and for loops.
    # The commands are kept in the run JSON (.worker/) as the log. They are read from the live stream (Codex and agy),
    # so a breach already stopped the worker mid-run (Live._command); this is the final record.
    if base == 'executor':
        cmds = live.commands if len(live.commands) >= len(res.get('commands') or []) else res['commands']   # agy only shows them live
        off = allow_violations(cmds, parse_allow(proj.get('exec_allow', '')))
        looped = command_loops(cmds, EXEC_LOOP_REPEAT)
        res['commands'] = cmds
        res['off_allowlist'] = off
        res['looped'] = looped
        res['over_budget'] = len(cmds) > a.max_commands
        if off:
            res['code'] = 4   # a command outside the allowlist is a scope breach, like an outside path
        res['denied'] = (res.get('denied') or []) + [f'OFF ALLOWLIST: {c}' for c in off]
        extra = ''
        if looped:
            extra += f" LOOP: ran `{looped}` >= {EXEC_LOOP_REPEAT} times; change tack."
        if res['over_budget']:
            extra += f" OVER BUDGET: {len(cmds)} commands > {a.max_commands}."
        if extra:
            res['error'] = ((res.get('error') or '') + ' |' + extra).strip(' |')
    res['check'] = check
    if base in WEB_BASES:   # a researcher that never searched may still name URLs: they were not read in this run
        res['web_uses'] = live.web_uses
        if res['code'] == 0 and not live.web_uses:
            res['error'] = ((res.get('error') or '') + ' | NO WEB LOOKUP: the worker searched nothing, so any URL it names '
                            'was not read in this run (recon.py merge marks those CVEs unverified).').strip(' |')
    own, outside = split_scope(changed_since(before, git_snapshot(ROOT)), a.files)
    res.update({'role': a.role, 'seconds': int(time.monotonic() - start), 'tried': tried, 'run_file': run_file,
                'log_file': f'.worker/run-{run_id}.log',
                'model': w['m'], 'family': family(w['m']), 'after': a.after,
                'files_changed': [c.strip() for c in diff_stat(ROOT, own)],
                'files_outside': [c.strip() for c in diff_stat(ROOT, outside)]})
    for k in ('conversation_id', 'response', 'error', 'input_tokens', 'cache_read_tokens', 'output_tokens', 'thinking_tokens'):
        res.setdefault(k, None)

    live.who = 'delegate'
    live.say(f"=== {LABELS.get(res['code'], res['code'])} after {res['seconds']}s | files: "
             + ('; '.join(res['files_changed']) or 'none'))
    json_out = json.dumps(res, indent=2, ensure_ascii=False)
    for f in (run_file, '.worker/last.json'):
        (ROOT / f).write_text(json_out, encoding='utf-8')
    if a.json:
        print(json_out)
    else:
        none = lambda v: '' if v is None else v
        print(f"[{LABELS.get(res['code'], res['code'])}] {a.role} via {res['worker']} | {res['seconds']}s | "
              f"in {none(res['input_tokens'])} (+cache {none(res['cache_read_tokens'])}) out {none(res['output_tokens'])}")
        if len(tried) > 1:
            print('tried: ' + ', '.join(tried))
        print('files: ' + ('; '.join(res['files_changed']) or 'none'))
        if res['files_outside']:
            print('NOT IN --files (another worker, this one broke its scope, or a secret file): ' + '; '.join(res['files_outside']))
        if check:
            n = check.get('fix_rounds')
            print('check: ' + check_text(check) + (f" | after {n} fix round{'s' if n > 1 else ''}" if n else ''))
            if check.get('passed') is False:
                print(check['output'])
        if base in WEB_BASES:
            print(f"web: {len(res.get('web_uses') or [])} search(es)/fetch(es)")
        if base == 'executor':
            flags = [f for f, on in (('LOOP', res.get('looped')), ('OVER BUDGET', res.get('over_budget')),
                                     (f"{len(res.get('off_allowlist') or [])} OFF ALLOWLIST", res.get('off_allowlist'))) if on]
            print(f"exec: {len(res.get('commands') or [])} commands run" + (' | ' + ', '.join(flags) if flags else ''))
        if res['denied']:
            print('denied: ' + '; '.join(res['denied']))
        if res['error']:
            print(f"error: {res['error']}")
        print(f"conversation: {none(res['conversation_id'])} | saved: {run_file} (run id {run_file[12:20]})")
        print('--- report ---')
        print(str(none(res['response'])).strip())
    return int(res['code'])


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Fail as e:
        print(f'ERROR: {e}', file=sys.stderr)
        sys.exit(e.code)
