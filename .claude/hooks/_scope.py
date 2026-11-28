#!/usr/bin/env python3
"""Shared helpers for the hooks: which engagement is active, is its SCOPE.md authorised, is a target in scope.

Fail closed: anything unreadable or unclear counts as NOT authorised. Hooks print status only, never target lists.
"""
import ipaddress
import json
import re
import shlex
from pathlib import Path
from urllib.parse import urlparse

try:
    LEVELS = json.loads((Path(__file__).resolve().parents[2] / 'agent' / 'scope_levels.json').read_text(encoding='utf-8-sig'))
except (OSError, ValueError):
    LEVELS = {'levels': {}, 'tool_level': {}, 'destructive_patterns': {'patterns': []}}

IPV4 = re.compile(r'(?<![\w.])(\d{1,3}(?:\.\d{1,3}){3})(?:/(\d{1,2}))?(?![\w.])')
URL = re.compile(r'\b[a-z][a-z0-9+.-]*://[^\s"\'<>]+', re.I)
HOST = re.compile(r'(?<![\w@/.-])([a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+)(?![\w-])', re.I)
FILE_EXT = {'xml', 'txt', 'json', 'gnmap', 'nmap', 'log', 'lst', 'py', 'sh', 'md', 'csv', 'html', 'yml', 'yaml',
            'conf', 'cfg', 'out', 'pcap', 'zip', 'gz', 'bin', 'exe', 'dll', 'php', 'js', 'rb', 'pl', 'ini', 'db'}


def engagements(root):
    base = Path(root) / 'engagements'
    try:
        return sorted(p for p in base.iterdir() if p.is_dir() and not p.name.startswith(('_', '.')))
    except OSError:
        return []


def read(path):
    try:
        return Path(path).read_text(encoding='utf-8-sig', errors='replace')
    except OSError:
        return ''


def authorised(scope_text):
    """True only when SCOPE.md exists, no longer says NOT AUTHORISED YET and the ownership line is not 'no'."""
    if not scope_text or re.search(r'NOT AUTHORI[SZ]ED YET', scope_text, re.I):
        return False
    m = re.search(r'\(yes\s*/\s*no\)\*{0,2}\s*[-—:]*\s*`?(yes|no)`?', scope_text, re.I)
    return bool(m) and m.group(1).lower() == 'yes'


def in_scope_section(scope_text):
    m = re.search(r'^##\s*In scope[^\n]*\n(.*?)(?=^##\s|\Z)', scope_text, re.I | re.M | re.S)
    return m.group(1) if m else ''


def parse_targets(scope_text):
    """-> (networks, hostnames) from the bulleted items of the In scope section (backticked item, else first word)."""
    nets, hosts = [], set()
    for line in in_scope_section(scope_text).splitlines():
        if not line.lstrip().startswith(('-', '*')):
            continue
        ticks = re.findall(r'`([^`]+)`', line)
        words = line.lstrip('-* ').split()
        first = ticks[0] if ticks else (words[0] if words else '')
        if not first or first.startswith('<'):
            continue
        for tok in re.split(r'[\s,]+', first):
            tok = tok.strip().lower()
            if '://' in tok:
                tok = urlparse(tok).hostname or ''
            if not tok:
                continue
            try:
                nets.append(ipaddress.ip_network(tok, strict=False))
                continue
            except ValueError:
                pass
            if re.fullmatch(r'[a-z0-9.-]+\.[a-z0-9-]+', tok):
                hosts.add(tok)
    return nets, hosts


def status(root):
    """-> (state, names): state in 'none' | 'unauthorised' | 'ambiguous' | 'ok'; names = engagement folder names."""
    eng = engagements(root)
    if not eng:
        return 'none', []
    ok = [e for e in eng if authorised(read(e / 'SCOPE.md'))]
    if not ok:
        return 'unauthorised', [e.name for e in eng]
    if len(eng) > 1:
        return 'ambiguous', [e.name for e in eng]
    return 'ok', [ok[0].name]


def targets_in(text, strict_hosts=True):
    """Hosts/IPs a command or tool input mentions: ([ipv4 strings], [hostnames])."""
    ips, hosts = [], []
    for m in URL.finditer(text):
        h = urlparse(m.group(0)).hostname
        if h:
            (ips if re.fullmatch(r'[\d.]+', h) else hosts).append(h.lower())
    bare = URL.sub(' ', text)
    for m in IPV4.finditer(bare):
        try:
            ipaddress.ip_address(m.group(1))
            ips.append(m.group(1) + (('/' + m.group(2)) if m.group(2) else ''))
        except ValueError:
            pass
    if strict_hosts:
        for m in HOST.finditer(bare):
            h = m.group(1).lower()
            if h.rsplit('.', 1)[-1] in FILE_EXT or re.fullmatch(r'[\d.]+', h):
                continue
            hosts.append(h)
    return ips, hosts


def out_of_scope(root, text):
    """Targets in text that an authorised engagement's SCOPE.md does not list. [] when all are in scope."""
    nets, hosts = [], set()
    for e in engagements(root):
        body = read(e / 'SCOPE.md')
        if authorised(body):
            n, h = parse_targets(body)
            nets += n
            hosts |= h
    ips, names = targets_in(text)
    bad = []
    for ip in ips:
        try:
            net = ipaddress.ip_network(ip, strict=False)
        except ValueError:
            continue
        if not any(net.version == n.version and net.subnet_of(n) for n in nets):
            bad.append(ip)
    for h in names:
        if not any(h == s or h.endswith('.' + s) for s in hosts):
            bad.append(h)
    return sorted(set(bad))


def command_binary(cmd):
    """The first program a command runs (for error messages): the first bare word past env VAR=... and wrappers."""
    progs = command_programs(cmd)
    return (progs[0] if progs else '')


SHELLS = {'sh', 'bash', 'dash', 'zsh', 'ksh'}
# Wrappers that run the next word as the program, with their options that take an argument (skipped with it).
WRAPPERS = {'sudo': {'-u', '-g', '-C', '-D', '-h', '-p', '-U', '-r', '-t', '-T', '--user', '--group', '--prompt'},
            'doas': {'-u', '-C'}, 'env': {'-u', '-C', '-S', '--unset', '--chdir', '--split-string'},
            'nice': {'-n', '--adjustment'}, 'stdbuf': {'-i', '-o', '-e'}, 'timeout': {'-s', '-k', '--signal', '--kill-after'},
            'command': set(), 'nohup': set(), 'time': {'-f', '-o'}}
SHELL_WORDS = {'!', '{', '}', 'then', 'do', 'else', 'fi', 'done'}
SEPARATORS = {';', '&', '&&', '|', '||', '|&', '(', ')', ';;'}
REDIRECTS = {'<', '>', '>>', '<<', '<<<', '>&', '&>', '&>>', '>|', '<>', '<&'}
HIDDEN_COMMAND = re.compile(r'\$\(|`|<\(|>\(')   # $(...), backticks, <(...), >(...)
BIN_DIRS = ('/usr/bin/', '/bin/', '/usr/sbin/', '/sbin/', '/usr/local/bin/', '/usr/local/sbin/')
ASSIGN = re.compile(r'^([A-Za-z_]\w*)=')
RISKY_VARS = re.compile(r'^(PATH|LD_\w+|BASH_ENV|ENV|IFS|SHELLOPTS|BASHOPTS|PS4|PROMPT_COMMAND)$')


def _program(tok):
    if '/' not in tok and '\\' not in tok:
        return tok
    folder, _, name = tok.rpartition('/')
    return name if folder + '/' in BIN_DIRS else tok


def command_programs(cmd, depth=0):
    """Every program a shell command line runs: each part of a pipe or list (; && || | &), past VAR=... and wrappers
    (sudo, env, timeout, ...), and inside bash -c '...'. None = can't tell (a command hidden in $(...) or backticks,
    an odd operator, bad quoting, PATH=/LD_* set, too deep): the caller treats that as needing the top level."""
    if isinstance(cmd, (list, tuple)):
        cmd = shlex.join(str(c) for c in cmd)
    text = str(cmd or '')
    if depth > 3 or HIDDEN_COMMAND.search(text):
        return None
    try:
        lex = shlex.shlex(text.replace('\r', ' ').replace('\n', ' ; '), posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        lex.commenters = ''
        toks = list(lex)
    except ValueError:
        return None
    progs, i, start = [], 0, True
    while i < len(toks):
        t = toks[i]
        if t and all(ch in ';&|()<>' for ch in t):
            if t in REDIRECTS:
                i += 2
            elif t in SEPARATORS:
                start, i = True, i + 1
            else:
                return None
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
                    return None
                i += 2 if toks[i] in takes_arg else 1
            if t == 'timeout' and i < len(toks):
                i += 1
            continue
        name = _program(t)
        start = False
        i += 1
        if name in SHELLS:
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


def _tool_level(binary):
    """The tier of one program name: impacket-* is 3; otherwise its highest level in scope_levels.json (0 = ungated)."""
    b = Path(str(binary or '')).name
    if not b:
        return 0
    if b.startswith('impacket-'):
        return 3
    best = 0
    for lvl, tools in (LEVELS.get('tool_level') or {}).items():
        if lvl.startswith('_'):
            continue
        if b in tools:
            best = max(best, int(lvl))
    return best


def _max_known_level():
    nums = [int(l) for l in (LEVELS.get('tool_level') or {}) if not l.startswith('_') and l.isdigit()]
    return max(nums) if nums else 4


def required_level(text):
    """Minimum engagement level a command needs: the highest tier among EVERY program it runs, so a benign first
    word can't smuggle a gated tool past (e.g. 'ls; nmap ...'). 0 = ungated. A command that can't be parsed safely
    is treated as needing the top known level (fail closed)."""
    progs = command_programs(text)
    if progs is None:
        return _max_known_level()
    best = 0
    for b in progs:
        best = max(best, _tool_level(b))
    return best


def mcp_required_level(tool_name):
    """Minimum level a HexStrike MCP tool needs, matched by tool name (e.g. mcp__hexstrike__nmap_scan -> 2)."""
    tn = (tool_name or '').lower().replace('_', '').replace('-', '').replace('.', '')
    best = 0
    for lvl, tools in (LEVELS.get('tool_level') or {}).items():
        if lvl.startswith('_'):
            continue
        for t in tools:
            if t and t.replace('.', '').replace('-', '') in tn:
                best = max(best, int(lvl))
    return best


def destructive_hit(text):
    """The first destructive pattern the text matches (refused below god-mode), else ''."""
    for p in ((LEVELS.get('destructive_patterns') or {}).get('patterns') or []):
        try:
            if re.search(p, text, re.I):
                return p
        except re.error:
            continue
    return ''


def level_name(n):
    return ((LEVELS.get('levels') or {}).get(str(n)) or {}).get('name', '?')


def level(root):
    """The authorised engagement's level (1-4) from its SCOPE.md. Authorised but no/garbled level, or none
    authorised: 1 (most restrictive). Fail closed."""
    for e in engagements(root):
        body = read(e / 'SCOPE.md')
        if authorised(body):
            m = re.search(r'^\s*[-*]*\s*\**level\b\**\s*[:\-—]\s*`?\**\s*([1-4])', body, re.I | re.M)
            return int(m.group(1)) if m else 1
    return 1


def exec_allow_over_level(root, lvl):
    """exec_allow tools (PROJECT.md) whose tier is above lvl: the executor must not be allowed to exceed the level."""
    m = re.search(r'^\s*exec_allow\s*:\s*(.*)$', read(Path(root) / 'PROJECT.md'), re.M)
    if not m:
        return []
    over = []
    for t in re.split(r'[\s,]+', m.group(1).strip()):
        if not t:
            continue
        r = required_level(Path(t).name)
        if r > lvl:
            over.append(Path(t).name + ' (needs L' + str(r) + ')')
    return over
