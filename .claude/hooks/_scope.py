#!/usr/bin/env python3
"""Shared helpers for the hooks: which engagement is active, is its SCOPE.md authorised, is a target in scope.

Fail closed: anything unreadable or unclear counts as NOT authorised. Hooks print status only, never target lists.
"""
import ipaddress
import re
from pathlib import Path
from urllib.parse import urlparse

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
